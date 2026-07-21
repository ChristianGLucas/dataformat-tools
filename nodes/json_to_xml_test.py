from gen.messages_pb2 import JsonToXmlRequest
from nodes.json_to_xml import json_to_xml
from nodes.testkit import assert_error, assert_ok, ax


def test_single_key_object_uses_that_key_as_root_ignoring_root_name():
    result = json_to_xml(
        ax(),
        JsonToXmlRequest(
            json='{"root":{"@a":"1","@b":"2","item":["x","y"]}}', root_name="ignored"
        ),
    )
    assert_ok(result)
    assert result.xml == '<root a="1" b="2">\n  <item>x</item>\n  <item>y</item>\n</root>'


def test_multi_key_object_requires_root_name():
    result = json_to_xml(ax(), JsonToXmlRequest(json='{"a":1,"b":2}'))
    assert_error(result, "INVALID_ARGUMENT")


def test_multi_key_object_with_root_name():
    result = json_to_xml(ax(), JsonToXmlRequest(json='{"a":1,"b":2}', root_name="root"))
    assert_ok(result)
    assert result.xml == "<root>\n  <a>1</a>\n  <b>2</b>\n</root>"


def test_scalar_with_root_name():
    result = json_to_xml(ax(), JsonToXmlRequest(json='"hello"', root_name="greeting"))
    assert_ok(result)
    assert result.xml == "<greeting>hello</greeting>"


def test_bool_and_null_rendering():
    result = json_to_xml(
        ax(), JsonToXmlRequest(json='{"root":{"a":true,"b":false,"c":null}}')
    )
    assert_ok(result)
    assert result.xml == (
        "<root>\n  <a>true</a>\n  <b>false</b>\n  <c />\n</root>"
    )


def test_invalid_root_name_is_invalid_argument():
    result = json_to_xml(ax(), JsonToXmlRequest(json='{"1bad":1}'))
    assert_error(result, "INVALID_ARGUMENT")


def test_malformed_json_is_invalid_input():
    result = json_to_xml(ax(), JsonToXmlRequest(json='{"a": }', root_name="root"))
    assert_error(result, "INVALID_INPUT")


def test_round_trips_with_xml_to_json():
    from gen.messages_pb2 import XmlToJsonRequest
    from nodes.xml_to_json import xml_to_json

    original_xml = '<root a="1" b="2"><item>x</item><item>y</item></root>'
    to_json = xml_to_json(ax(), XmlToJsonRequest(xml=original_xml))
    assert_ok(to_json)
    back_to_xml = json_to_xml(ax(), JsonToXmlRequest(json=to_json.json))
    assert_ok(back_to_xml)
    # Structurally equivalent (attribute order may differ in principle; here
    # it is preserved since Python dicts keep insertion order end to end).
    assert back_to_xml.xml == '<root a="1" b="2">\n  <item>x</item>\n  <item>y</item>\n</root>'
