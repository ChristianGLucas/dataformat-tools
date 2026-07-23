# dataformat-tools

Composable structured-data format-conversion nodes for the
[Axiom](https://axiomide.com) marketplace, published as
`christiangeorgelucas/dataformat-tools`.

Convert between JSON, YAML, TOML, and XML; validate each with line/column
error detail; pretty-print or minify each; and guess an unknown text's
format. JSON is the hub — every node either speaks JSON directly or converts
to/from it, so a conversion this package doesn't offer as its own node
(YAML↔TOML, XML↔TOML, XML↔YAML) composes by chaining two nodes in a flow
(e.g. `YamlToJson` → `JsonToToml`) instead.

Wraps [PyYAML](https://pyyaml.org/) (MIT, `safe_load`/`safe_dump` only),
[tomlkit](https://github.com/python-poetry/tomlkit) (MIT), and
[defusedxml](https://github.com/tiran/defusedxml) (PSFL) — each owns the
actual hard part (grammar, type resolution, tree building) for its format;
this package supplies the JSON-hub envelope, the size bound, and a
consistent error vocabulary. Fully offline, stateless, deterministic. No API
keys, no network, no secrets.

## Use it from your agent or app

Every node in this package is a **live, auto-scaling API endpoint** on the
[Axiom](https://axiomide.com) marketplace — call it from an AI agent or your own
code, with nothing to self-host.

**📦 See it on the marketplace:**
https://dev.axiomide.com/marketplace/christiangeorgelucas/dataformat-tools@0.1.0

**Hook it up to an AI agent (MCP).** Add Axiom's hosted MCP server to any MCP
client and every node becomes a typed tool your agent can call — search the
catalog, inspect a schema, and invoke it directly.

```bash
# Claude Code
claude mcp add --transport http axiom https://api.axiomide.com/mcp \
  --header "Authorization: Bearer $AXIOM_API_KEY"
```

Claude Desktop, Cursor, or any config-based client:

```json
{
  "mcpServers": {
    "axiom": {
      "type": "http",
      "url": "https://api.axiomide.com/mcp",
      "headers": { "Authorization": "Bearer YOUR_AXIOM_API_KEY" }
    }
  }
}
```

**Call it from the CLI.**

```bash
axiom invoke christiangeorgelucas/dataformat-tools/YamlToJson --input '{ ... }'
```

**Call it over HTTP.**

```bash
curl -X POST https://api.axiomide.com/invocations/v1/nodes/christiangeorgelucas/dataformat-tools/0.1.0/YamlToJson \
  -H "Authorization: Bearer $AXIOM_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{ ... }'
```

> Input/output schema for each node is on the marketplace page above, or via
> `axiom inspect node christiangeorgelucas/dataformat-tools/YamlToJson`.

### Get started free

Install the CLI:

```bash
# macOS / Linux — Homebrew
brew install axiomide/tap/axiom

# macOS / Linux — install script
curl -fsSL https://raw.githubusercontent.com/AxiomIDE/axiom-releases/main/install.sh | sh
```

**Windows:** download the `windows/amd64` `.zip` from the
[releases page](https://github.com/AxiomIDE/axiom-releases/releases), unzip it,
and put `axiom.exe` on your `PATH`.

Then `axiom version` to verify, `axiom login` (GitHub or Google) to authenticate,
and create an API key under **Console → API Keys**. Docs and sign-up at
**[axiomide.com](https://axiomide.com)**.

## Security

- **YAML** is parsed with PyYAML's `safe_load` only — never the default full
  `Loader`, which can construct arbitrary Python objects from crafted input
  (a known deserialization-RCE class, `!!python/object/apply:...` and
  friends). Verified by a hostile-input test that the tag is rejected, not
  executed.
- **XML** is parsed with `defusedxml.ElementTree.fromstring(text,
  forbid_dtd=True)`, which rejects **every** `<!DOCTYPE>` declaration
  outright — closing both XXE (external entity expansion reading local
  files / SSRF) and "billion laughs" (internal entity expansion exhausting
  memory) at the parser level, not by pattern-matching the input text.
- **Every text input** accepted by any node is capped at 5 MB
  (`MAX_INPUT_BYTES`, checked on the raw UTF-8 byte length before any
  parsing begins).
- Deeply nested input (a cost axis a byte-size cap does **not** bound) is
  handled by catching `RecursionError` around every parse/dump path —
  verified empirically that CPython's C-accelerated `json` decoder,
  PyYAML's pure-Python composer, and this package's own recursive XML↔dict
  conversion all raise a catchable `RecursionError` rather than crashing
  the process.
- Malformed input never crashes a node — every output message carries an
  `error` field, unset on success.

## The envelope

There's no single shared message across every node (a YAML document and a
TOML document are genuinely different texts), but the shape is uniform:
every node takes a small request message with the source text plus a few
options, and returns a `<Format>Result{ <format>: string, error: Error }` or
a `ValidateResult{ valid, error_message, line, column }`. See
`messages/messages.proto` for the exact fields.

## Nodes

| Node | Does |
|---|---|
| `YamlToJson` | YAML text → JSON text |
| `JsonToYaml` | JSON text → YAML text (block style) |
| `TomlToJson` | TOML text → JSON text |
| `JsonToToml` | JSON text → TOML text |
| `XmlToJson` | XML text → JSON text (`@attr`/`#text`/array convention) |
| `JsonToXml` | JSON text → XML text (inverse convention) |
| `ValidateJson` | Well-formed JSON? Line/column on failure |
| `ValidateYaml` | Well-formed YAML? Line/column on failure |
| `ValidateToml` | Well-formed TOML? Line/column on failure |
| `ValidateXml` | Well-formed XML? Line/column on failure |
| `FormatJson` | Pretty-print / minify / sort-keys JSON |
| `FormatYaml` | Canonicalize YAML formatting |
| `FormatToml` | Style-preserving pass-through, or sort-keys rebuild |
| `FormatXml` | Pretty-print (indent) / minify XML |
| `DetectFormat` | Guess json/yaml/toml/xml/unknown, with per-format scores |

## The XML ⇄ JSON convention

`XmlToJson`'s output is a JSON object with exactly one top-level key — the
root element's tag name:

```
<catalog version="2">
  <book id="1"><title>Dune</title></book>
  <book id="2"><title>Hyperion</title></book>
</catalog>
```
→
```json
{"catalog": {"@version": "2", "book": [
  {"@id": "1", "title": "Dune"},
  {"@id": "2", "title": "Hyperion"}
]}}
```

An attribute becomes an `"@name"` key; text alongside attributes/children
becomes `"#text"`; a text-only leaf becomes a bare string; repeated
same-tag siblings become an array. `JsonToXml` consumes exactly this
convention in reverse, so the pair round-trips. When the JSON isn't a
single-key object, `JsonToXml` needs `root_name` — see
`JsonToXmlRequest` in the proto for the precise rule.

## Behaviour worth knowing

**TOML has no null.** `JsonToToml` rejects any JSON `null` anywhere in the
document with `UNSUPPORTED_VALUE`, naming the exact JSON-pointer-ish path
(`$.a.b[1]`) — not just "conversion failed". It also rejects a JSON document
that isn't an object at the top level, since a TOML document is always a
table.

**TOML datetimes are one-way.** TOML's native offset-datetime /
local-datetime / local-date / local-time values become ISO-8601 strings in
`TomlToJson`'s output (JSON has no datetime type). Converting that string
back with `JsonToToml` produces a plain TOML *string*, not a native TOML
datetime — round-tripping through JSON does not preserve the type.

**YAML 1.1, not 1.2.** PyYAML's default resolver follows the YAML 1.1 core
schema: `yes`/`no`/`on`/`off` are booleans, octal is a bare `0` prefix
(`017` is 15, **not** YAML 1.2's `0o17` — that stays a string), and
`.inf`/`-.inf`/`.nan` are floats. `dataformat-tools` doesn't change any of
this; the oracle tests pin these exact resolutions against the spec, not
against the code.

**`FormatToml` is comment-preserving when it can be.** With `sort_keys`
false (the default), reformatting an already-well-formed document is a
validating pass-through — tomlkit's style/comment-preserving parse-and-dump
returns the source unchanged. Setting `sort_keys` rebuilds the document from
parsed plain values, which does **not** keep comments.

**Deterministic, not forcibly sorted.** Every conversion keeps the source's
own key order by default (itself a deterministic function of deterministic
input) rather than silently alphabetizing; pass `sort_keys` on the nodes
that offer it if you want alphabetical output instead.

## Errors

Nodes never raise. Every output carries an `error` field (or, for the
`Validate*` nodes, `valid`/`error_message`/`line`/`column`), unset on
success:

`INVALID_INPUT` · `UNSUPPORTED_VALUE` · `TOO_LARGE` · `INVALID_ARGUMENT` ·
`INTERNAL`

A traceback never reaches the caller. If a node faults unexpectedly it
returns `INTERNAL`, which says the fault is ours so you do not go debugging
your own input.

## Composing these nodes

`YamlToJson` → `JsonToToml` gives YAML→TOML with no node of its own needed;
the same pattern covers every format pair through the JSON hub. `XmlToJson`
composes naturally with any JSON-consuming package in the catalog (e.g.
`json-query-tools`' `filter`/`json` fields, `json-schema-tools`' `instance`
field) since its output is plain JSON text, not a bespoke type.

## Tests

```bash
axiom test
```

104 tests: a golden test per node, an error-path test per node, a hostile-
input suite (XXE, billion-laughs, the YAML RCE tag, oversized input, deep
nesting) exercised through the public nodes (not just the internal
helpers), and an independent-oracle suite that checks `TomlToJson` against
Python's own stdlib `tomllib` (a from-scratch, different implementation
from the tomlkit this package wraps), checks YAML type resolution against
the YAML 1.1 core-schema rules read from the spec, and checks the XML↔JSON
convention against a hand-traced expected value — none of it round-tripped
through this package's own code and compared to itself.

## Licence

MIT — see [LICENSE](LICENSE).

Wraps PyYAML (MIT), tomlkit (MIT), and defusedxml (PSFL) — each with zero
transitive dependencies of its own. No copyleft anywhere in the tree; see
[requirements.txt](requirements.txt). The verbatim license texts are
reproduced in [THIRD_PARTY_LICENSES.txt](THIRD_PARTY_LICENSES.txt).

Built for the Axiom marketplace.
