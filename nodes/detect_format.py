from gen.axiom_context import AxiomContext
from gen.messages_pb2 import DetectInput, DetectResult, Error, FormatScore
from nodes._shared import ConversionError, detect_format_scores


def detect_format(ax: AxiomContext, input: DetectInput) -> DetectResult:
    """Guess which of JSON/YAML/TOML/XML a text is, by attempting to parse it
    as each and scoring how confidently it matches (JSON/XML/TOML require an
    actual parse success; YAML is scored lowest among successful parses
    because its grammar also accepts plain scalar text every other format
    would reject). Returns the best guess plus every format's own score.
    """
    try:
        scores = detect_format_scores(input.text)
        candidates = [FormatScore(format=fmt, confidence=conf) for fmt, conf in scores]
        best_format, best_conf = scores[0]
        if best_conf <= 0.0:
            best_format = "unknown"
        return DetectResult(format=best_format, confidence=best_conf, candidates=candidates)
    except ConversionError as exc:
        ax.log.info("detect_format rejected input", code=exc.code)
        return DetectResult(format="unknown", error=Error(code=exc.code, message=exc.message))
    except Exception as exc:
        ax.log.error("detect_format faulted", error=str(exc))
        return DetectResult(format="unknown", error=Error(code="INTERNAL", message="internal error"))
