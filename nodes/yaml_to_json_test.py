from gen.messages_pb2 import YamlToJsonRequest
from nodes.testkit import assert_error, assert_ok, ax
from nodes.yaml_to_json import yaml_to_json


def test_scalar_mapping_and_sequence():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: 1\nb:\n  - x\n  - y\nc: true\n"))
    assert_ok(result)
    assert result.json == '{"a":1,"b":["x","y"],"c":true}'


def test_sort_keys_alphabetizes_output():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="b: 1\na: 2\n", sort_keys=True))
    assert_ok(result)
    assert result.json == '{"a":2,"b":1}'


def test_default_preserves_source_key_order():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="b: 1\na: 2\n", sort_keys=False))
    assert_ok(result)
    assert result.json == '{"b":1,"a":2}'


def test_malformed_yaml_is_invalid_input():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: [1, 2\n"))
    assert_error(result, "INVALID_INPUT")


def test_multi_document_stream_is_rejected():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="---\na: 1\n---\nb: 2\n"))
    assert_error(result, "INVALID_INPUT")


def test_null_scalar_becomes_json_null():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml="a: null\nb: ~\n"))
    assert_ok(result)
    assert result.json == '{"a":null,"b":null}'


def test_empty_input_is_json_null():
    result = yaml_to_json(ax(), YamlToJsonRequest(yaml=""))
    assert_ok(result)
    assert result.json == "null"
