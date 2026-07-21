from gen.messages_pb2 import JsonInput
from nodes.testkit import assert_invalid, assert_valid, ax
from nodes.validate_json import validate_json


def test_well_formed_json_is_valid():
    assert_valid(validate_json(ax(), JsonInput(json='{"a": [1, 2, 3]}')))


def test_malformed_json_reports_line_and_column():
    result = validate_json(ax(), JsonInput(json='{"a": }'))
    assert_invalid(result)
    assert result.line == 1
    assert result.column == 7


def test_trailing_garbage_is_invalid():
    assert_invalid(validate_json(ax(), JsonInput(json='{"a": 1} extra')))


def test_empty_string_is_invalid():
    assert_invalid(validate_json(ax(), JsonInput(json="")))
