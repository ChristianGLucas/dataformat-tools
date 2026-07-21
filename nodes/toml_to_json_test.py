from gen.messages_pb2 import TomlToJsonRequest
from nodes.testkit import assert_error, assert_ok, ax
from nodes.toml_to_json import toml_to_json


def test_table_and_array():
    result = toml_to_json(ax(), TomlToJsonRequest(toml='a = 1\n[b]\nc = "x"\nd = [1,2,3]\n'))
    assert_ok(result)
    assert result.json == '{"a":1,"b":{"c":"x","d":[1,2,3]}}'


def test_sort_keys_alphabetizes_output():
    result = toml_to_json(ax(), TomlToJsonRequest(toml='b = 1\na = 2\n', sort_keys=True))
    assert_ok(result)
    assert result.json == '{"a":2,"b":1}'


def test_datetime_becomes_iso8601_string():
    result = toml_to_json(ax(), TomlToJsonRequest(toml="d = 2024-01-01T00:00:00Z\n"))
    assert_ok(result)
    assert result.json == '{"d":"2024-01-01T00:00:00+00:00"}'


def test_malformed_toml_is_invalid_input():
    result = toml_to_json(ax(), TomlToJsonRequest(toml="a = [1, 2\n"))
    assert_error(result, "INVALID_INPUT")


def test_local_date_becomes_iso_string():
    result = toml_to_json(ax(), TomlToJsonRequest(toml="d = 2024-01-01\n"))
    assert_ok(result)
    assert result.json == '{"d":"2024-01-01"}'
