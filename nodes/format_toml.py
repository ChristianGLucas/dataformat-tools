import tomlkit

from gen.axiom_context import AxiomContext
from gen.messages_pb2 import Error, FormatTomlRequest, TomlResult
from nodes._shared import ConversionError, dump_toml, parse_toml_document


def format_toml(ax: AxiomContext, input: FormatTomlRequest) -> TomlResult:
    """Re-serialize TOML text through tomlkit. With sort_keys false
    (default), reformatting preserves the source's original formatting and
    comments unchanged (tomlkit is style-preserving) — a validating
    pass-through for already-well-formed TOML. With sort_keys true, the
    document is rebuilt from parsed values with keys alphabetized, which
    does NOT preserve comments. Also validates: malformed TOML is
    INVALID_INPUT. Input over 5 MB is TOO_LARGE.
    """
    try:
        doc = parse_toml_document(input.toml)
        if input.sort_keys:
            toml_text = dump_toml(doc.unwrap(), sort_keys=True)
        else:
            toml_text = tomlkit.dumps(doc)
        return TomlResult(toml=toml_text)
    except ConversionError as exc:
        ax.log.info("format_toml rejected input", code=exc.code)
        return TomlResult(error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("format_toml faulted", error=str(exc))
        return TomlResult(error=Error(code="INTERNAL", message="internal error"))
