from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ValidateResult, YamlInput
from nodes._shared import ConversionError, parse_yaml


def validate_yaml(ax: AxiomContext, input: YamlInput) -> ValidateResult:
    """Check whether text is well-formed YAML (via safe_load), reporting the
    syntax error's line and column when it is not. Input over 5 MB is
    reported via valid=false rather than parsed.
    """
    try:
        parse_yaml(input.yaml)
        return ValidateResult(valid=True)
    except ConversionError as exc:
        return ValidateResult(
            valid=False, error_message=exc.message, line=exc.line, column=exc.column
        )
    except Exception as exc:
        ax.log.error("validate_yaml faulted", error=str(exc))
        return ValidateResult(valid=False, error_message="internal error")
