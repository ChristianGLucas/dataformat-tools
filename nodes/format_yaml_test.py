from gen.messages_pb2 import FormatYamlRequest
from nodes.format_yaml import format_yaml
from nodes.testkit import assert_error, assert_ok, ax


def test_reformats_flow_style_to_block_style():
    result = format_yaml(ax(), FormatYamlRequest(yaml="a: {b: 1, c: 2}\n"))
    assert_ok(result)
    assert result.yaml == "a:\n  b: 1\n  c: 2\n"


def test_sort_keys_alphabetizes():
    result = format_yaml(ax(), FormatYamlRequest(yaml="b: 1\na: 2\n", sort_keys=True))
    assert_ok(result)
    assert result.yaml == "a: 2\nb: 1\n"


def test_malformed_yaml_is_invalid_input():
    result = format_yaml(ax(), FormatYamlRequest(yaml="a: [1, 2\n"))
    assert_error(result, "INVALID_INPUT")


def test_custom_indent_width():
    result = format_yaml(ax(), FormatYamlRequest(yaml="a:\n  b: 1\n", indent=4))
    assert_ok(result)
    assert result.yaml == "a:\n    b: 1\n"
