from gen.messages_pb2 import FormatJsonRequest
from nodes.format_json import format_json
from nodes.testkit import assert_error, assert_ok, ax


def test_pretty_indents():
    result = format_json(ax(), FormatJsonRequest(json='{"b":1,"a":2}', pretty=True, indent=4, sort_keys=True))
    assert_ok(result)
    assert result.json == '{\n    "a": 2,\n    "b": 1\n}'


def test_compact_minifies():
    result = format_json(ax(), FormatJsonRequest(json='{ "b" : 1 ,  "a":2 }', pretty=False))
    assert_ok(result)
    assert result.json == '{"b":1,"a":2}'


def test_default_indent_is_two_when_zero():
    result = format_json(ax(), FormatJsonRequest(json='{"a":1}', pretty=True, indent=0))
    assert_ok(result)
    assert result.json == '{\n  "a": 1\n}'


def test_malformed_json_is_invalid_input():
    result = format_json(ax(), FormatJsonRequest(json='{"a": }'))
    assert_error(result, "INVALID_INPUT")
