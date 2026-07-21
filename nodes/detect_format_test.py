from gen.messages_pb2 import DetectInput
from nodes.detect_format import detect_format
from nodes.testkit import ax


def test_json_object_detected_as_json():
    result = detect_format(ax(), DetectInput(text='{"a":1}'))
    assert result.format == "json"
    assert result.confidence == 0.99


def test_yaml_mapping_detected_as_yaml():
    result = detect_format(ax(), DetectInput(text="a: 1\nb: 2\n"))
    assert result.format == "yaml"


def test_toml_table_detected_as_toml():
    result = detect_format(ax(), DetectInput(text="a = 1\n[b]\nc = 2\n"))
    assert result.format == "toml"


def test_xml_detected_as_xml():
    result = detect_format(ax(), DetectInput(text="<a>1</a>"))
    assert result.format == "xml"


def test_candidates_are_sorted_descending_and_cover_all_four():
    result = detect_format(ax(), DetectInput(text='{"a":1}'))
    formats = [c.format for c in result.candidates]
    assert set(formats) == {"json", "yaml", "toml", "xml"}
    confidences = [c.confidence for c in result.candidates]
    assert confidences == sorted(confidences, reverse=True)
    assert result.candidates[0].format == "json"


def test_genuinely_unparseable_input_is_unknown():
    # A tab character makes this invalid YAML block-sequence indentation
    # (YAML forbids tabs for indentation), and it is not valid JSON, TOML,
    # or XML either.
    result = detect_format(ax(), DetectInput(text="\tfoo: [unclosed"))
    assert result.format == "unknown"
    assert result.confidence == 0.0


def test_tie_break_prefers_json_over_yaml():
    # A JSON object also happens to be a syntactically valid (if unusual)
    # YAML mapping; json's parse succeeding scores strictly higher, so the
    # tie-break order is exercised by score, not literally equal scores
    # here -- this asserts the documented outcome (json wins) end to end.
    result = detect_format(ax(), DetectInput(text='{"a": 1, "b": 2}'))
    assert result.format == "json"
