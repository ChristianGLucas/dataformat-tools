from gen.axiom_context import AxiomContext
from gen.messages_pb2 import JsonInput, ValidateResult
from nodes._shared import ConversionError, parse_json


def validate_json(ax: AxiomContext, input: JsonInput) -> ValidateResult:
    """Check whether text is well-formed JSON, reporting the syntax error's
    line and column when it is not. Input over 5 MB is reported via
    valid=false rather than parsed.
    """
    try:
        parse_json(input.json)
        return ValidateResult(valid=True)
    except ConversionError as exc:
        return ValidateResult(
            valid=False, error_message=exc.message, line=exc.line, column=exc.column
        )
    except Exception as exc:
        ax.log.error("validate_json faulted", error=str(exc))
        return ValidateResult(valid=False, error_message="internal error")
