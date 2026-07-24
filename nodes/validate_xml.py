from gen.axiom_context import AxiomContext
from gen.messages_pb2 import ValidateResult, XmlInput
from nodes._shared import ConversionError, parse_xml


def validate_xml(ax: AxiomContext, input: XmlInput) -> ValidateResult:
    """Check whether text is well-formed XML, parsed with defusedxml (any
    DOCTYPE is itself a validation failure, not a security exception — it is
    reported the same as any other syntax error), reporting the error's line
    and column when malformed.
    """
    try:
        parse_xml(input.xml)
        return ValidateResult(valid=True)
    except ConversionError as exc:
        return ValidateResult(
            valid=False, error_message=exc.message, line=exc.line, column=exc.column
        )
    except Exception as exc:
        ax.log.error("validate_xml faulted", error=str(exc))
        return ValidateResult(valid=False, error_message="internal error")
