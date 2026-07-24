from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, FormatYamlRequest, YamlResult
from nodes._shared import ConversionError, dump_yaml, parse_yaml


def format_yaml(ax: AxiomContext, input: FormatYamlRequest) -> YamlResult:
    """Re-serialize YAML text through PyYAML's safe_load/safe_dump,
    canonicalizing its block-style formatting to a fixed indent width,
    optionally alphabetizing keys. Also validates: malformed YAML is
    INVALID_INPUT.
    """
    try:
        value = parse_yaml(input.yaml)
        yaml_text = dump_yaml(value, sort_keys=input.sort_keys, indent=input.indent)
        return YamlResult(yaml=yaml_text)
    except ConversionError as exc:
        ax.log.info("format_yaml rejected input", code=exc.code)
        return YamlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("format_yaml faulted", error=str(exc))
        return YamlResult(error=Error(code="INTERNAL", message="internal error"))
