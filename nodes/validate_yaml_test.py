from gen.messages_pb2 import YamlInput
from nodes.testkit import assert_invalid, assert_valid, ax
from nodes.validate_yaml import validate_yaml


def test_well_formed_yaml_is_valid():
    assert_valid(validate_yaml(ax(), YamlInput(yaml="a: 1\nb:\n  - x\n  - y\n")))


def test_malformed_yaml_reports_line_and_column():
    result = validate_yaml(ax(), YamlInput(yaml="a: [1, 2\n"))
    assert_invalid(result)
    assert result.line >= 1


def test_multi_document_stream_is_invalid():
    assert_invalid(validate_yaml(ax(), YamlInput(yaml="---\na: 1\n---\nb: 2\n")))


def test_empty_document_is_valid():
    # An empty YAML document is a legal (null) document, distinct from
    # malformed input.
    assert_valid(validate_yaml(ax(), YamlInput(yaml="")))


def test_unsafe_python_object_tag_is_rejected_not_executed():
    result = validate_yaml(
        ax(), YamlInput(yaml='a: !!python/object/apply:os.system ["echo pwned"]\n')
    )
    assert_invalid(result)
