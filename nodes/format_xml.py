from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, FormatXmlRequest, XmlResult
from nodes._shared import ConversionError, dump_xml, parse_xml


def format_xml(ax: AxiomContext, input: FormatXmlRequest) -> XmlResult:
    """Re-serialize XML text (parsed with defusedxml) as pretty-printed
    (indented, one element per line) or minified (no insignificant
    inter-element whitespace) XML. Also validates: malformed XML or a
    DOCTYPE is INVALID_INPUT.
    """
    try:
        root = parse_xml(input.xml)
        xml_text = dump_xml(root, pretty=input.pretty, indent=input.indent)
        return XmlResult(xml=xml_text)
    except ConversionError as exc:
        ax.log.info("format_xml rejected input", code=exc.code)
        return XmlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("format_xml faulted", error=str(exc))
        return XmlResult(error=Error(code="INTERNAL", message="internal error"))
