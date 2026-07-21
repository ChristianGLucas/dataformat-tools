from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonToTomlRequest, TomlResult
from nodes._shared import ConversionError, dump_toml, parse_json


def json_to_toml(ax: AxiomContext, input: JsonToTomlRequest) -> TomlResult:
    """Convert JSON text to a TOML document via tomlkit. The JSON must decode
    to an object at the top level (TOML documents are always a table) and
    must not contain a JSON null anywhere (TOML has no null) — either
    violation is UNSUPPORTED_VALUE, naming the offending location. Object
    keys keep source order unless sort_keys is set. Malformed JSON or input
    over 5 MB is rejected with a structured error rather than converted.
    """
    try:
        value = parse_json(input.json)
        toml_text = dump_toml(value, sort_keys=input.sort_keys)
        return TomlResult(toml=toml_text)
    except ConversionError as exc:
        ax.log.info("json_to_toml rejected input", code=exc.code)
        return TomlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("json_to_toml faulted", error=str(exc))
        return TomlResult(error=Error(code="INTERNAL", message="internal error"))
