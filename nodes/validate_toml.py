from gen.axiom_context import AxiomContext
from gen.messages_pb2 import TomlInput, ValidateResult
from nodes._shared import ConversionError, parse_toml


def validate_toml(ax: AxiomContext, input: TomlInput) -> ValidateResult:
    """Check whether text is well-formed TOML, reporting the syntax error's
    line and column when it is not. Input over 5 MB is reported via
    valid=false rather than parsed.
    """
    try:
        parse_toml(input.toml)
        return ValidateResult(valid=True)
    except ConversionError as exc:
        return ValidateResult(
            valid=False, error_message=exc.message, line=exc.line, column=exc.column
        )
    except Exception as exc:
        ax.log.error("validate_toml faulted", error=str(exc))
        return ValidateResult(valid=False, error_message="internal error")
