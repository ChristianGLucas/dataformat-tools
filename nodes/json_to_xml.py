from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonToXmlRequest, XmlResult
from nodes._shared import ConversionError, dump_xml, json_value_to_xml, parse_json


def json_to_xml(ax: AxiomContext, input: JsonToXmlRequest) -> XmlResult:
    """Convert JSON text to an XML document (indented, 2-space output),
    inverse of XmlToJson's convention ("@name" keys become attributes, a
    "#text" key becomes text content, array values become repeated sibling
    elements). When the JSON is an object with exactly one top-level key,
    that key names the root element and root_name is ignored; otherwise
    root_name is required (INVALID_ARGUMENT if missing or not a valid XML
    name). Malformed JSON is rejected with a structured
    error rather than converted.
    """
    try:
        value = parse_json(input.json)
        elem = json_value_to_xml(value, input.root_name)
        xml_text = dump_xml(elem, pretty=True, indent=2)
        return XmlResult(xml=xml_text)
    except ConversionError as exc:
        ax.log.info("json_to_xml rejected input", code=exc.code)
        return XmlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("json_to_xml faulted", error=str(exc))
        return XmlResult(error=Error(code="INTERNAL", message="internal error"))
