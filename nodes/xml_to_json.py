from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonResult, XmlToJsonRequest
from nodes._shared import ConversionError, dump_json, parse_xml, xml_to_json_value


def xml_to_json(ax: AxiomContext, input: XmlToJsonRequest) -> JsonResult:
    """Convert an XML document to JSON text, parsed with defusedxml (any
    DOCTYPE — internal or external — is rejected outright, closing both XXE
    and billion-laughs at the parser level). The result is a JSON object with
    exactly one top-level key, the root element's tag name; an element's
    attributes become "@name" keys, text content alongside attributes/
    children becomes a "#text" key, a text-only leaf element becomes a bare
    JSON string, and repeated same-tag sibling elements become a JSON array —
    the same convention JsonToXml consumes, so the pair round-trips.
    Malformed/non-well-formed XML, a DOCTYPE, or input over 5 MB is rejected
    with a structured error rather than converted.
    """
    try:
        root = parse_xml(input.xml)
        value = xml_to_json_value(root)
        json_text = dump_json(value, pretty=False)
        return JsonResult(json=json_text)
    except ConversionError as exc:
        ax.log.info("xml_to_json rejected input", code=exc.code)
        return JsonResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("xml_to_json faulted", error=str(exc))
        return JsonResult(error=Error(code="INTERNAL", message="internal error"))
