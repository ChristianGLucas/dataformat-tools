from gen.messages_pb2 import FormatXmlRequest
from nodes.format_xml import format_xml
from nodes.testkit import assert_error, assert_ok, ax


def test_pretty_indents_one_element_per_line():
    result = format_xml(ax(), FormatXmlRequest(xml="<root><item>x</item><item>y</item></root>", pretty=True))
    assert_ok(result)
    assert result.xml == "<root>\n  <item>x</item>\n  <item>y</item>\n</root>"


def test_minify_strips_insignificant_whitespace():
    result = format_xml(
        ax(),
        FormatXmlRequest(xml="<root>\n  <item>x</item>\n  <item>y</item>\n</root>\n", pretty=False),
    )
    assert_ok(result)
    assert result.xml == "<root><item>x</item><item>y</item></root>"


def test_custom_indent_width():
    result = format_xml(ax(), FormatXmlRequest(xml="<root><item>x</item></root>", pretty=True, indent=4))
    assert_ok(result)
    assert result.xml == "<root>\n    <item>x</item>\n</root>"


def test_malformed_xml_is_invalid_input():
    result = format_xml(ax(), FormatXmlRequest(xml="<a><b></a>"))
    assert_error(result, "INVALID_INPUT")


def test_doctype_is_invalid_input():
    result = format_xml(
        ax(),
        FormatXmlRequest(
            xml='<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY x SYSTEM "file:///etc/passwd">]><foo>&x;</foo>'
        ),
    )
    assert_error(result, "INVALID_INPUT")
