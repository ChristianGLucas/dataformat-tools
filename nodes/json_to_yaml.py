from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonToYamlRequest, YamlResult
from nodes._shared import ConversionError, dump_yaml, parse_json


def json_to_yaml(ax: AxiomContext, input: JsonToYamlRequest) -> YamlResult:
    """Convert JSON text to a YAML document (block style, 2-space indent), via
    PyYAML's safe_dump. Object keys keep source order unless sort_keys is
    set. Malformed JSON or input over 5 MB is rejected with a structured
    error rather than converted.
    """
    try:
        value = parse_json(input.json)
        yaml_text = dump_yaml(value, sort_keys=input.sort_keys)
        return YamlResult(yaml=yaml_text)
    except ConversionError as exc:
        ax.log.info("json_to_yaml rejected input", code=exc.code)
        return YamlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("json_to_yaml faulted", error=str(exc))
        return YamlResult(error=Error(code="INTERNAL", message="internal error"))
