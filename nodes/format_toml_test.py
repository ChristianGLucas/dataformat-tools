from gen.messages_pb2 import FormatTomlRequest
from nodes.format_toml import format_toml
from nodes.testkit import assert_error, assert_ok, ax


def test_default_pass_through_preserves_comments_and_formatting():
    src = '# a comment\na = 1  # inline\n\n[b]\nc = "x"\n'
    result = format_toml(ax(), FormatTomlRequest(toml=src))
    assert_ok(result)
    assert result.toml == src


def test_sort_keys_rebuilds_without_comments():
    src = "# a comment\nb = 1\na = 2\n"
    result = format_toml(ax(), FormatTomlRequest(toml=src, sort_keys=True))
    assert_ok(result)
    assert result.toml == "a = 2\nb = 1\n"
    assert "#" not in result.toml


def test_malformed_toml_is_invalid_input():
    result = format_toml(ax(), FormatTomlRequest(toml="a = [1, 2\n"))
    assert_error(result, "INVALID_INPUT")
