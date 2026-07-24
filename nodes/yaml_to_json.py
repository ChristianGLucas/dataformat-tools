from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, JsonResult, YamlToJsonRequest
from nodes._shared import ConversionError, dump_json, parse_yaml


def yaml_to_json(ax: AxiomContext, input: YamlToJsonRequest) -> JsonResult:
    """Convert a YAML document to JSON text, parsed with PyYAML's safe_load
    (never the full Loader, which can construct arbitrary Python objects from
    crafted input). Object keys keep source order unless sort_keys is set. A
    multi-document YAML stream ("---" separated) is
    rejected with a structured error rather than parsed.
    """
    try:
        value = parse_yaml(input.yaml)
        json_text = dump_json(value, pretty=False, sort_keys=input.sort_keys)
        return JsonResult(json=json_text)
    except ConversionError as exc:
        ax.log.info("yaml_to_json rejected input", code=exc.code)
        return JsonResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("yaml_to_json faulted", error=str(exc))
        return JsonResult(error=Error(code="INTERNAL", message="internal error"))
