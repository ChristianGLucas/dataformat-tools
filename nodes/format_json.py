from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, FormatJsonRequest, JsonResult
from nodes._shared import ConversionError, dump_json, parse_json


def format_json(ax: AxiomContext, input: FormatJsonRequest) -> JsonResult:
    """Re-serialize JSON text as pretty-printed (indented) or compact
    (minified, single-line) JSON, optionally alphabetizing keys. Also
    validates: malformed JSON is INVALID_INPUT. Input over 5 MB is
    TOO_LARGE.
    """
    try:
        value = parse_json(input.json)
        json_text = dump_json(
            value, pretty=input.pretty, indent=input.indent, sort_keys=input.sort_keys
        )
        return JsonResult(json=json_text)
    except ConversionError as exc:
        ax.log.info("format_json rejected input", code=exc.code)
        return JsonResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("format_json faulted", error=str(exc))
        return JsonResult(error=Error(code="INTERNAL", message="internal error"))
