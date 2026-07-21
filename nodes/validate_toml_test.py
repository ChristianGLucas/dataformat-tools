from gen.messages_pb2 import TomlInput
from nodes.testkit import assert_invalid, assert_valid, ax
from nodes.validate_toml import validate_toml


def test_well_formed_toml_is_valid():
    assert_valid(validate_toml(ax(), TomlInput(toml='a = 1\n[b]\nc = "x"\n')))


def test_malformed_toml_reports_a_reason():
    result = validate_toml(ax(), TomlInput(toml="a = [1, 2\n"))
    assert_invalid(result)


def test_bare_key_without_value_is_invalid():
    assert_invalid(validate_toml(ax(), TomlInput(toml="a\n")))


def test_empty_document_is_valid():
    assert_valid(validate_toml(ax(), TomlInput(toml="")))
