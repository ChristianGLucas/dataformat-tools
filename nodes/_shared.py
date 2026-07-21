"""Shared parsing/serialization helpers for christiangeorgelucas/dataformat-tools.

Every node funnels its parsing through the helpers here so the security
posture (safe YAML loading, hardened XML parsing, the 5 MB size bound) and
the JSON<->XML dict convention are defined exactly once, not once per node.

SECURITY, read this before touching parse_yaml/parse_xml:
  - YAML: yaml.safe_load ONLY. yaml.load()/yaml.Loader (the non-safe default)
    can construct arbitrary Python objects from crafted input via tags like
    !!python/object:... — a known deserialization-RCE class. safe_load uses
    yaml.SafeLoader, which only ever builds plain dict/list/str/int/float/
    bool/None/datetime/date.
  - XML: defusedxml.ElementTree.fromstring ONLY, never xml.etree directly on
    untrusted text. defusedxml rejects any DOCTYPE declaration outright
    (EntitiesForbidden/DTDForbidden), which closes both XXE (external entity
    expansion reading local files / SSRF) and "billion laughs" (internal
    entity expansion exhausting memory) at the parser level.
  - Every parse_* function checks input size FIRST, before any parsing work,
    against MAX_INPUT_BYTES.
  - Every parse_* function also tolerates RecursionError (deeply nested
    input can exceed Python's recursion limit — verified empirically for
    the C-accelerated json decoder, PyYAML's pure-Python composer, and our
    own recursive XML<->dict conversion: all three raise a catchable
    RecursionError rather than crashing the process) and reports it as a
    structured INVALID_INPUT rather than letting it propagate as a raw
    traceback.
"""

from __future__ import annotations

import copy
import json as _json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, time
from typing import Any

import tomlkit
import yaml
from defusedxml.common import DTDForbidden, EntitiesForbidden, ExternalReferenceForbidden
import defusedxml.ElementTree as DefusedET
from tomlkit.exceptions import TOMLKitError

MAX_INPUT_BYTES = 5_000_000  # 5 MB, enforced before any parse begins.


class ConversionError(Exception):
    """A structured (code, message[, line, column]) failure a node can catch
    and turn directly into its output message's `error`/`ValidateResult` shape.
    """

    def __init__(self, code: str, message: str, line: int = 0, column: int = 0):
        super().__init__(message)
        self.code = code
        self.message = message
        self.line = line
        self.column = column


def check_size(text: str) -> None:
    n = len(text.encode("utf-8", errors="surrogatepass"))
    if n > MAX_INPUT_BYTES:
        raise ConversionError(
            "TOO_LARGE",
            f"input is {n} bytes, exceeding the {MAX_INPUT_BYTES}-byte limit",
        )


def json_type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


# ── YAML ─────────────────────────────────────────────────────────────────


def _yaml_error_pos(exc: "yaml.YAMLError") -> tuple[int, int]:
    mark = getattr(exc, "problem_mark", None)
    if mark is not None:
        return mark.line + 1, mark.column + 1
    return 0, 0


def parse_yaml(text: str) -> Any:
    check_size(text)
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        line, col = _yaml_error_pos(exc)
        raise ConversionError("INVALID_INPUT", str(exc), line, col) from exc
    except RecursionError as exc:
        raise ConversionError("INVALID_INPUT", "document nesting too deep") from exc


def dump_yaml(value: Any, sort_keys: bool = False, indent: int = 2) -> str:
    try:
        return yaml.safe_dump(
            value,
            sort_keys=sort_keys,
            indent=indent or 2,
            allow_unicode=True,
            default_flow_style=False,
        )
    except yaml.YAMLError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", str(exc)) from exc
    except RecursionError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", "value nesting too deep to serialize") from exc


# ── JSON ─────────────────────────────────────────────────────────────────


def _json_default(o: Any) -> str:
    if isinstance(o, (datetime, date, time)):
        return o.isoformat()
    raise TypeError(f"object of type {type(o).__name__} is not JSON serializable")


def parse_json(text: str) -> Any:
    check_size(text)
    try:
        return _json.loads(text)
    except _json.JSONDecodeError as exc:
        raise ConversionError("INVALID_INPUT", exc.msg, exc.lineno, exc.colno) from exc
    except RecursionError as exc:
        raise ConversionError("INVALID_INPUT", "document nesting too deep") from exc


def dump_json(value: Any, pretty: bool = False, indent: int = 2, sort_keys: bool = False) -> str:
    try:
        if pretty:
            return _json.dumps(
                value, indent=indent or 2, sort_keys=sort_keys, default=_json_default, ensure_ascii=False
            )
        return _json.dumps(
            value, separators=(",", ":"), sort_keys=sort_keys, default=_json_default, ensure_ascii=False
        )
    except (TypeError, ValueError) as exc:
        raise ConversionError("UNSUPPORTED_VALUE", str(exc)) from exc
    except RecursionError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", "value nesting too deep to serialize") from exc


# ── TOML ─────────────────────────────────────────────────────────────────


def _find_null(value: Any, path: str = "$") -> str | None:
    if value is None:
        return path
    if isinstance(value, dict):
        for k, v in value.items():
            found = _find_null(v, f"{path}.{k}")
            if found is not None:
                return found
    elif isinstance(value, list):
        for i, v in enumerate(value):
            found = _find_null(v, f"{path}[{i}]")
            if found is not None:
                return found
    return None


def _sort_recursive(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _sort_recursive(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_sort_recursive(v) for v in value]
    return value


def parse_toml_document(text: str) -> "tomlkit.TOMLDocument":
    """Parse TOML preserving the original style/comments (tomlkit's own
    document type) -- used by FormatToml's non-sort-keys pass-through so
    reformatting a well-formed document is a validating no-op, not a
    lossy rebuild. Prefer parse_toml() below for anything that needs a
    plain JSON-compatible value.
    """
    check_size(text)
    try:
        return tomlkit.parse(text)
    except TOMLKitError as exc:
        line = getattr(exc, "line", 0) or 0
        col = getattr(exc, "col", None)
        col = (col + 1) if isinstance(col, int) else 0
        raise ConversionError("INVALID_INPUT", str(exc), line, col) from exc
    except RecursionError as exc:
        raise ConversionError("INVALID_INPUT", "document nesting too deep") from exc


def parse_toml(text: str) -> Any:
    return parse_toml_document(text).unwrap()


def dump_toml(value: Any, sort_keys: bool = False) -> str:
    if not isinstance(value, dict):
        raise ConversionError(
            "UNSUPPORTED_VALUE",
            f"TOML requires a top-level table (object); got {json_type_name(value)}",
        )
    null_path = _find_null(value)
    if null_path is not None:
        raise ConversionError("UNSUPPORTED_VALUE", f"TOML has no null; found one at {null_path}")
    try:
        data = _sort_recursive(value) if sort_keys else value
        return tomlkit.dumps(data)
    except (TOMLKitError, TypeError, ValueError) as exc:
        raise ConversionError("UNSUPPORTED_VALUE", str(exc)) from exc
    except RecursionError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", "value nesting too deep to serialize") from exc


# ── XML ──────────────────────────────────────────────────────────────────

_XML_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.\-]*$")


def valid_xml_name(name: str) -> bool:
    if not name or not _XML_NAME_RE.match(name):
        return False
    if name[:3].lower() == "xml":
        return False
    return True


def parse_xml(text: str) -> ET.Element:
    check_size(text)
    try:
        # forbid_dtd=True rejects EVERY DOCTYPE outright, not just ones that
        # declare entities -- defusedxml's own default (forbid_dtd=False)
        # only blocks entity declarations/external references, which leaves
        # a harmless bare "<!DOCTYPE foo>" through. Rejecting all DOCTYPEs
        # unconditionally is simpler to reason about and document than
        # trying to enumerate which DOCTYPE shapes are "safe".
        return DefusedET.fromstring(text, forbid_dtd=True)
    except (EntitiesForbidden, DTDForbidden, ExternalReferenceForbidden) as exc:
        raise ConversionError("INVALID_INPUT", f"DOCTYPE/entity declarations are not permitted: {exc}") from exc
    except ET.ParseError as exc:
        # NB: exc.msg is the underlying xml.parsers.expat.ExpatError OBJECT,
        # not a string (a cpython ElementTree quirk) -- str(exc) is the
        # clean message text.
        line, col = exc.position if exc.position else (0, 0)
        raise ConversionError("INVALID_INPUT", str(exc), line, col) from exc
    except RecursionError as exc:
        raise ConversionError("INVALID_INPUT", "document nesting too deep") from exc


def _scalar_to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def elem_to_value(elem: ET.Element) -> Any:
    """Convert one XML element (recursively) to a JSON-compatible value.

    Convention (symmetric with value_to_elem below): an attribute "foo"
    becomes key "@foo"; text content alongside attributes/children becomes
    key "#text"; a leaf element with no attributes and no children becomes a
    bare string (its stripped text, "" if empty); repeated same-tag sibling
    elements become a JSON array.
    """
    children = list(elem)
    attrs = dict(elem.attrib)
    text = (elem.text or "").strip()

    if not children and not attrs:
        return text

    result: dict[str, Any] = {f"@{k}": v for k, v in attrs.items()}

    child_order: list[str] = []
    child_map: dict[str, list[Any]] = {}
    for child in children:
        if child.tag not in child_map:
            child_order.append(child.tag)
            child_map[child.tag] = []
        child_map[child.tag].append(elem_to_value(child))

    for tag in child_order:
        values = child_map[tag]
        result[tag] = values[0] if len(values) == 1 else values

    if text:
        result["#text"] = text

    return result


def xml_to_json_value(root: ET.Element) -> dict:
    try:
        return {root.tag: elem_to_value(root)}
    except RecursionError as exc:
        raise ConversionError("INVALID_INPUT", "document nesting too deep") from exc


def value_to_elem(tag: str, value: Any) -> ET.Element:
    elem = ET.Element(tag)
    if isinstance(value, dict):
        for k, v in value.items():
            if k.startswith("@"):
                elem.set(k[1:], _scalar_to_str(v))
            elif k == "#text":
                elem.text = _scalar_to_str(v)
            elif isinstance(v, list):
                for item in v:
                    elem.append(value_to_elem(k, item))
            else:
                elem.append(value_to_elem(k, v))
    elif isinstance(value, list):
        # A bare list directly as an element's content (no enclosing key to
        # name the children) -- each item becomes an "item" child. Only
        # reachable at the document root when JsonToXml's root_name path
        # hands a top-level JSON array straight to the root element.
        for item in value:
            elem.append(value_to_elem("item", item))
    elif value is None:
        pass  # empty element
    else:
        elem.text = _scalar_to_str(value)
    return elem


def json_value_to_xml(value: Any, root_name: str) -> ET.Element:
    if isinstance(value, dict) and len(value) == 1:
        (tag, content), = value.items()
    elif root_name:
        tag, content = root_name, value
    else:
        raise ConversionError(
            "INVALID_ARGUMENT",
            "root_name is required unless json is an object with exactly one top-level key",
        )
    if not valid_xml_name(tag):
        raise ConversionError("INVALID_ARGUMENT", f"{tag!r} is not a valid XML name")
    try:
        return value_to_elem(tag, content)
    except RecursionError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", "value nesting too deep to serialize") from exc


def _strip_whitespace(elem: ET.Element) -> None:
    if elem.text is not None and elem.text.strip() == "":
        elem.text = None
    if elem.tail is not None and elem.tail.strip() == "":
        elem.tail = None
    for child in elem:
        _strip_whitespace(child)


# ── DetectFormat ─────────────────────────────────────────────────────────


def detect_format_scores(text: str) -> list[tuple[str, float]]:
    """Score `text` against each of json/xml/toml/yaml, highest first (ties
    broken json > xml > toml > yaml, per DetectFormat's documented rule).
    Does NOT raise ConversionError for a bad/ambiguous parse -- a format
    that fails to parse simply scores 0.0. The caller is still responsible
    for the TOO_LARGE size check before calling this.
    """
    scores: dict[str, float] = {"json": 0.0, "xml": 0.0, "toml": 0.0, "yaml": 0.0}

    try:
        _json.loads(text)
        scores["json"] = 0.99
    except (_json.JSONDecodeError, RecursionError):
        pass

    try:
        DefusedET.fromstring(text)
        scores["xml"] = 0.95
    except Exception:
        pass

    try:
        doc = tomlkit.parse(text)
        scores["toml"] = 0.9 if len(doc) > 0 else 0.3
    except Exception:
        pass

    try:
        value = yaml.safe_load(text)
        if isinstance(value, (dict, list)):
            scores["yaml"] = 0.6
        elif value is None:
            scores["yaml"] = 0.1
        else:
            scores["yaml"] = 0.2
    except Exception:
        pass

    order = {"json": 0, "xml": 1, "toml": 2, "yaml": 3}
    return sorted(scores.items(), key=lambda kv: (-kv[1], order[kv[0]]))


def dump_xml(elem: ET.Element, pretty: bool = True, indent: int = 2) -> str:
    elem = copy.deepcopy(elem)
    try:
        if pretty:
            ET.indent(elem, space=" " * (indent or 2))
        else:
            _strip_whitespace(elem)
        return ET.tostring(elem, encoding="unicode")
    except RecursionError as exc:
        raise ConversionError("UNSUPPORTED_VALUE", "value nesting too deep to serialize") from exc
