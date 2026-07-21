from gen.messages_pb2 import JsonToTomlRequest
from nodes.json_to_toml import json_to_toml
from nodes.testkit import assert_error, assert_ok, ax


def test_object_with_nested_table_and_array():
    result = json_to_toml(
        ax(), JsonToTomlRequest(json='{"a": 1, "b": {"c": "x", "d": [1,2,3]}}')
    )
    assert_ok(result)
    assert result.toml == 'a = 1\n\n[b]\nc = "x"\nd = [1, 2, 3]\n'


def test_top_level_array_is_unsupported_value():
    result = json_to_toml(ax(), JsonToTomlRequest(json="[1,2,3]"))
    assert_error(result, "UNSUPPORTED_VALUE")


def test_top_level_scalar_is_unsupported_value():
    result = json_to_toml(ax(), JsonToTomlRequest(json='"just a string"'))
    assert_error(result, "UNSUPPORTED_VALUE")


def test_null_anywhere_is_unsupported_value_naming_the_path():
    result = json_to_toml(ax(), JsonToTomlRequest(json='{"a": {"b": [1, null, 3]}}'))
    assert_error(result, "UNSUPPORTED_VALUE")
    assert "$.a.b[1]" in result.error.message


def test_malformed_json_is_invalid_input():
    result = json_to_toml(ax(), JsonToTomlRequest(json='{"a": }'))
    assert_error(result, "INVALID_INPUT")


def test_sort_keys_alphabetizes_output():
    result = json_to_toml(ax(), JsonToTomlRequest(json='{"b": 1, "a": 2}', sort_keys=True))
    assert_ok(result)
    assert result.toml == "a = 2\nb = 1\n"


def test_output_reparses_to_the_same_value_via_tomlkit():
    import tomlkit

    src = {"name": "widget", "count": 3, "tags": ["a", "b"], "nested": {"x": True}}
    result = json_to_toml(ax(), JsonToTomlRequest(json='{"name":"widget","count":3,"tags":["a","b"],"nested":{"x":true}}'))
    assert_ok(result)
    assert tomlkit.parse(result.toml).unwrap() == src
