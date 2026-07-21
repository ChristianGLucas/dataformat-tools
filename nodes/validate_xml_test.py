from gen.messages_pb2 import XmlInput
from nodes.testkit import assert_invalid, assert_valid, ax
from nodes.validate_xml import validate_xml


def test_well_formed_xml_is_valid():
    assert_valid(validate_xml(ax(), XmlInput(xml="<a><b>1</b></a>")))


def test_mismatched_tags_report_line_and_column():
    result = validate_xml(ax(), XmlInput(xml="<a><b></a>"))
    assert_invalid(result)
    assert result.line == 1
    assert result.column >= 1


def test_doctype_is_invalid_not_a_crash():
    result = validate_xml(
        ax(),
        XmlInput(
            xml='<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY x SYSTEM "file:///etc/passwd">]><foo>&x;</foo>'
        ),
    )
    assert_invalid(result)


def test_no_root_element_is_invalid():
    assert_invalid(validate_xml(ax(), XmlInput(xml="")))


def test_multiple_root_elements_is_invalid():
    assert_invalid(validate_xml(ax(), XmlInput(xml="<a/><b/>")))
