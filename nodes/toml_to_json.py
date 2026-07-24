from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonResult, TomlToJsonRequest
from nodes._shared import ConversionError, dump_json, parse_toml


def toml_to_json(ax: AxiomContext, input: TomlToJsonRequest) -> JsonResult:
    """Convert a TOML document to JSON text via tomlkit. Object keys keep
    source order unless sort_keys is set. TOML's native datetime/date/time
    values become ISO-8601 strings (JSON has no datetime type). Malformed
    TOML is rejected with a structured error rather than
    converted.
    """
    try:
        value = parse_toml(input.toml)
        json_text = dump_json(value, pretty=False, sort_keys=input.sort_keys)
        return JsonResult(json=json_text)
    except ConversionError as exc:
        ax.log.info("toml_to_json rejected input", code=exc.code)
        return JsonResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("toml_to_json faulted", error=str(exc))
        return JsonResult(error=Error(code="INTERNAL", message="internal error"))
