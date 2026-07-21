from gen.messages_pb2 import JsonToYamlRequest
from nodes.json_to_yaml import json_to_yaml
from nodes.testkit import assert_error, assert_ok, ax


def test_object_becomes_block_style_yaml():
    result = json_to_yaml(ax(), JsonToYamlRequest(json='{"b":1,"a":2}'))
    assert_ok(result)
    assert result.yaml == "b: 1\na: 2\n"


def test_sort_keys_alphabetizes_output():
    result = json_to_yaml(ax(), JsonToYamlRequest(json='{"b":1,"a":2}', sort_keys=True))
    assert_ok(result)
    assert result.yaml == "a: 2\nb: 1\n"


def test_malformed_json_is_invalid_input():
    result = json_to_yaml(ax(), JsonToYamlRequest(json='{"a": }'))
    assert_error(result, "INVALID_INPUT")


def test_nested_structure_round_trips_through_yaml_load():
    import yaml as pyyaml

    result = json_to_yaml(
        ax(), JsonToYamlRequest(json='{"a":{"b":[1,2,3]},"c":null}')
    )
    assert_ok(result)
    assert pyyaml.safe_load(result.yaml) == {"a": {"b": [1, 2, 3]}, "c": None}
