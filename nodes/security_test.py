"""Hostile-input tests: the attack classes this package is explicitly
supposed to close (see messages.proto's package-level security note),
exercised through the actual public nodes -- not just the _shared helpers
-- so a regression in wiring, not just in the helper, would be caught.
"""

from gen.messages_pb2 import (
    FormatXmlRequest,
    JsonToTomlRequest,
    ValidateResult,
    XmlInput,
    XmlToJsonRequest,
    YamlInput,
    YamlToJsonRequest,
)
from nodes.format_xml import format_xml
from nodes.testkit import assert_error, assert_invalid, ax
from nodes.validate_xml import validate_xml
from nodes.validate_yaml import validate_yaml
from nodes.xml_to_json import xml_to_json
from nodes.yaml_to_json import yaml_to_json

XXE_PAYLOAD = (
    '<?xml version="1.0"?>'
    '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
    "<foo>&xxe;</foo>"
)

BILLION_LAUGHS_PAYLOAD = (
    '<?xml version="1.0"?>'
    "<!DOCTYPE lolz ["
    ' <!ENTITY lol "lol">'
    " <!ELEMENT lolz (#PCDATA)>"
    ' <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">'
    ' <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">'
    "]>"
    "<lolz>&lol2;</lolz>"
)

YAML_RCE_PAYLOAD = 'a: !!python/object/apply:os.system ["echo pwned"]\n'


def test_xxe_is_rejected_not_read_via_xml_to_json():
    result = xml_to_json(ax(), XmlToJsonRequest(xml=XXE_PAYLOAD))
    assert_error(result, "INVALID_INPUT")
    assert "passwd" not in result.json  # the file was never read


def test_xxe_is_rejected_via_validate_xml():
    assert_invalid(validate_xml(ax(), XmlInput(xml=XXE_PAYLOAD)))


def test_xxe_is_rejected_via_format_xml():
    result = format_xml(ax(), FormatXmlRequest(xml=XXE_PAYLOAD))
    assert_error(result, "INVALID_INPUT")


def test_billion_laughs_is_rejected_before_expansion():
    result = xml_to_json(ax(), XmlToJsonRequest(xml=BILLION_LAUGHS_PAYLOAD))
    assert_error(result, "INVALID_INPUT")


def test_billion_laughs_is_rejected_via_validate_xml():
    assert_invalid(validate_xml(ax(), XmlInput(xml=BILLION_LAUGHS_PAYLOAD)))


def test_plain_doctype_with_no_entities_is_still_rejected():
    # Not every DOCTYPE declares an entity, but the package rejects DOCTYPE
    # outright (never parses it to find out whether it's "safe") -- that is
    # the whole point of not pattern-matching the input.
    payload = '<?xml version="1.0"?><!DOCTYPE foo><foo>bar</foo>'
    assert_invalid(validate_xml(ax(), XmlInput(xml=payload)))


def test_yaml_unsafe_object_tag_never_executes_and_is_rejected():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml=YAML_RCE_PAYLOAD))
    assert_error(result, "INVALID_INPUT")


def test_yaml_unsafe_object_tag_rejected_via_validate_yaml():
    assert_invalid(validate_yaml(ax(), YamlInput(yaml=YAML_RCE_PAYLOAD)))


def test_large_yaml_input_does_not_crash():
    # No payload size limit is imposed by this node -- the platform owns
    # that. A large-but-well-formed document parses cleanly.
    large = "a: " + ("x" * 6_000_000)
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml=large))
    assert not result.error.code


def test_large_xml_input_does_not_crash():
    large = "<a>" + ("x" * 6_000_000) + "</a>"
    result = xml_to_json(ax(), XmlToJsonRequest(xml=large))
    assert not result.error.code


def test_deeply_nested_json_does_not_crash_the_process():
    # CPython's C-accelerated json decoder raises a catchable RecursionError
    # for pathologically deep nesting rather than crashing (verified
    # empirically for this package's target runtime) -- this asserts the
    # node-level contract: a structured error, never a raw traceback/crash.
    from gen.messages_pb2 import JsonInput
    from nodes.validate_json import validate_json

    deep = "[" * 200_000 + "1" + "]" * 200_000
    result = validate_json(ax(), JsonInput(json=deep))
    assert isinstance(result, ValidateResult)
    assert not result.valid


def test_json_null_cannot_smuggle_into_toml_as_a_bare_word():
    # TOML has no null literal; make sure the guard is on the VALUE, not a
    # naive string search that a key or string containing "null" would trip.
    result_ok_string = JsonToTomlRequest(json='{"a": "null"}')
    from nodes.json_to_toml import json_to_toml

    ok = json_to_toml(ax(), result_ok_string)
    assert not ok.error.code
    assert ok.toml == 'a = "null"\n'

    rejected = json_to_toml(ax(), JsonToTomlRequest(json='{"a": null}'))
    assert_error(rejected, "UNSUPPORTED_VALUE")
