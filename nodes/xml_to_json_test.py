from gen.messages_pb2 import XmlToJsonRequest
from nodes.testkit import assert_error, assert_ok, ax
from nodes.xml_to_json import xml_to_json


def test_attributes_and_repeated_children_become_array():
    result = xml_to_json(
        ax(), XmlToJsonRequest(xml='<root a="1" b="2"><item>x</item><item>y</item></root>')
    )
    assert_ok(result)
    assert result.json == '{"root":{"@a":"1","@b":"2","item":["x","y"]}}'


def test_leaf_element_becomes_bare_string():
    result = xml_to_json(ax(), XmlToJsonRequest(xml="<name>Alice</name>"))
    assert_ok(result)
    assert result.json == '{"name":"Alice"}'


def test_text_alongside_attribute_uses_text_key():
    result = xml_to_json(ax(), XmlToJsonRequest(xml='<p id="1">hello</p>'))
    assert_ok(result)
    assert result.json == '{"p":{"@id":"1","#text":"hello"}}'


def test_single_child_is_not_wrapped_in_array():
    result = xml_to_json(ax(), XmlToJsonRequest(xml="<a><b>1</b></a>"))
    assert_ok(result)
    assert result.json == '{"a":{"b":"1"}}'


def test_empty_leaf_element_becomes_empty_string():
    result = xml_to_json(ax(), XmlToJsonRequest(xml="<a></a>"))
    assert_ok(result)
    assert result.json == '{"a":""}'


def test_malformed_xml_is_invalid_input():
    result = xml_to_json(ax(), XmlToJsonRequest(xml="<a><b></a>"))
    assert_error(result, "INVALID_INPUT")


def test_doctype_is_rejected_as_invalid_input_not_a_crash():
    result = xml_to_json(
        ax(),
        XmlToJsonRequest(
            xml='<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY x SYSTEM "file:///etc/passwd">]><foo>&x;</foo>'
        ),
    )
    assert_error(result, "INVALID_INPUT")
