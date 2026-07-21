"""Independent-oracle tests.

These do NOT just round-trip our own conversion through itself. Each checks
against something independent of the code under test:

  - TOML: Python's stdlib `tomllib` (a from-scratch, read-only TOML parser
    shipped with CPython since 3.11 -- a DIFFERENT implementation from the
    tomlkit this package wraps) parses the same source and must agree with
    what TomlToJson produces.
  - YAML: expected values are the YAML 1.1 core-schema type-resolution rules
    themselves (yes/no/on/off as bool, 0-prefix octal, 0x hex, .inf/.nan),
    read directly from the spec/PyYAML's documented resolver -- not derived
    by running this package's own code and asserting it matches itself.
  - XML: expected JSON is hand-traced from the documented @attr/#text/array
    convention against the raw XML text, not produced by calling our own
    elem_to_value and comparing it to itself.
"""

import tomllib

from gen.messages_pb2 import (
    JsonToTomlRequest,
    TomlToJsonRequest,
    XmlToJsonRequest,
    YamlToJsonRequest,
)
from nodes._shared import dump_json, parse_json, parse_yaml
from nodes.json_to_toml import json_to_toml
from nodes.testkit import assert_ok, ax
from nodes.toml_to_json import toml_to_json
from nodes.xml_to_json import xml_to_json
from nodes.yaml_to_json import yaml_to_json


# ── TOML, oracled against stdlib tomllib ────────────────────────────────


def _toml_oracle_case(toml_src: str):
    oracle = tomllib.loads(toml_src)
    result = toml_to_json(ax(), TomlToJsonRequest(toml=toml_src))
    assert_ok(result)
    ours = parse_json(result.json)
    assert ours == oracle, f"stdlib tomllib got {oracle!r}, TomlToJson got {ours!r}"


def test_toml_to_json_agrees_with_stdlib_tomllib_on_scalars_and_arrays():
    _toml_oracle_case('name = "widget"\ncount = 3\npi = 3.14\nok = true\n')
    _toml_oracle_case("nums = [1, 2, 3]\nmixed = [1, \"two\", 3.0]\n")


def test_toml_to_json_agrees_with_stdlib_tomllib_on_nested_tables():
    _toml_oracle_case(
        '[server]\nhost = "localhost"\nport = 8080\n\n'
        '[server.tls]\nenabled = true\ncert = "/etc/cert.pem"\n'
    )


def test_toml_to_json_agrees_with_stdlib_tomllib_on_array_of_tables():
    _toml_oracle_case(
        '[[fruit]]\nname = "apple"\n\n[[fruit]]\nname = "banana"\n'
    )


def test_toml_to_json_agrees_with_stdlib_tomllib_on_inline_tables():
    _toml_oracle_case('point = { x = 1, y = 2 }\n')


def test_json_to_toml_output_reparses_via_stdlib_tomllib_to_the_source_value():
    source = {"a": 1, "b": {"c": [1, 2, 3], "d": "text"}, "e": True}
    result = json_to_toml(
        ax(),
        JsonToTomlRequest(json='{"a":1,"b":{"c":[1,2,3],"d":"text"},"e":true}'),
    )
    assert_ok(result)
    reparsed = tomllib.loads(result.toml)
    assert reparsed == source


# ── YAML, oracled against the YAML 1.1 core-schema resolution rules ─────


def test_yaml_1_1_bool_words_resolve_per_spec():
    for word, expected in [
        ("yes", True), ("no", False), ("on", True), ("off", False),
        ("true", True), ("false", False), ("True", True), ("FALSE", False),
    ]:
        result = yaml_to_json(ax(), YamlToJsonRequest(yaml=f"a: {word}\n"))
        assert_ok(result)
        assert parse_json(result.json)["a"] is expected, word


def test_yaml_1_1_null_forms_resolve_per_spec():
    for text in ["null", "~", "Null", "NULL"]:
        result = yaml_to_json(ax(), YamlToJsonRequest(yaml=f"a: {text}\n"))
        assert_ok(result)
        assert parse_json(result.json)["a"] is None, text


def test_yaml_1_1_octal_and_hex_int_resolve_per_spec():
    # YAML 1.1's octal form is a bare "0" prefix (017 == 15 decimal) -- NOT
    # YAML 1.2's "0o17" (which PyYAML's 1.1 resolver leaves as a string).
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: 017\nb: 0x1A\n"))
    assert_ok(result)
    v = parse_json(result.json)
    assert v["a"] == 15
    assert v["b"] == 26


def test_yaml_1_1_inf_and_nan_resolve_to_float_per_spec():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: .inf\nb: -.inf\n"))
    assert_ok(result)
    v = parse_json(result.json)
    assert v["a"] == float("inf")
    assert v["b"] == float("-inf")


def test_yaml_1_1_underscored_int_resolves_per_spec():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: 1_000_000\n"))
    assert_ok(result)
    assert parse_json(result.json)["a"] == 1_000_000


# ── XML, oracled by hand-tracing the documented convention ─────────────


def test_xml_to_json_matches_a_hand_traced_conversion():
    xml = (
        '<catalog version="2">'
        "<book id=\"1\"><title>Dune</title><author>Herbert</author></book>"
        "<book id=\"2\"><title>Hyperion</title><author>Simmons</author></book>"
        "</catalog>"
    )
    # Hand-traced per the documented rule: attributes -> "@name", repeated
    # same-tag siblings -> array, leaf element with no attrs/children -> bare
    # string.
    expected = {
        "catalog": {
            "@version": "2",
            "book": [
                {"@id": "1", "title": "Dune", "author": "Herbert"},
                {"@id": "2", "title": "Hyperion", "author": "Simmons"},
            ],
        }
    }
    result = xml_to_json(ax(), XmlToJsonRequest(xml=xml))
    assert_ok(result)
    assert parse_json(result.json) == expected


def test_xml_to_json_mixed_text_and_children_matches_hand_trace():
    xml = '<note priority="high">Remember <b>this</b></note>'
    # A parent with BOTH text ("Remember ") and a child element: per the
    # documented rule, text alongside children goes under "#text".
    expected = {"note": {"@priority": "high", "#text": "Remember", "b": "this"}}
    result = xml_to_json(ax(), XmlToJsonRequest(xml=xml))
    assert_ok(result)
    assert parse_json(result.json) == expected
