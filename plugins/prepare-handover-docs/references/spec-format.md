# Content spec format (what the engine consumes)

Each tab is one JSON spec. `scripts/build_doc.py` turns it into a native Google Docs
tab. Save specs into the **target project** at `docs/handover/specs/<tab>.json`.

```json
{
  "docId": "<target google doc id>",
  "tabTitle": "<tab name, e.g. Env Details>",
  "blocks": [ ...ordered blocks... ]
}
```

`docId` may be a placeholder (`REPLACE_DOC_ID`) in the file — pass the real id with
`--doc <id>` at write time. `tabTitle` can likewise be overridden with `--tab`.

## Block types

| type | fields | renders as |
| --- | --- | --- |
| `h1` | `text` | Heading 1 (page/tab title) |
| `h2` | `text` | Heading 2 |
| `comp` | `text` | Heading 3 |
| `label` | `text` | Bold section label |
| `para` | `text` | Plain paragraph |
| `bullet` | `text`, `level` (0/1/2), optional `bold` | Nested bullet |
| `detail` | `text` | Indented plain line (nests under the last bullet) |
| `figlink` | `text`, `url` | `[text]` rendered as a hyperlink |
| `figline` | `prefix`, `text`, `url` | `<prefix> [text]` with the bracket part linked |
| `image` | `path`, optional `size_pt {width,height}` | Embeds a local image (needs `drive` scope) |
| `spacer` | — | One blank line |

## Rules & constraints

- **No `table` type.** Render matrices (accounts/ownership, versions) as **nested
  bullets** — a `bullet` level 0 header with `level` 1 rows.
- **Links show the URL as the text** for handover clarity: set a `figline`/`figlink`
  `text` to the same string as its `url` (that is how this plugin renders Drive/console
  links — a raw, clickable URL rather than link-text).
- **Exactly one `h1`** per tab, first, as the visible title.
- **Never put a secret value in any block.** Only key names, public identifiers,
  fingerprints, links, and vault pointers.
- The engine **appends a new tab** every run; **tab titles must be unique** in the doc.
- The engine self-verifies after writing, but that check can pass on a truncated tail —
  the skill adds its own last-block read-back check (see interaction-protocol.md).

## Running the engine

Dry-run (no network, validates ranges):

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_doc.py" --spec docs/handover/specs/<tab>.json --dry-run
```

Live write (creates + verifies the tab):

```
SSL_CERT_FILE="$(python3 -m certifi 2>/dev/null || echo /etc/ssl/cert.pem)" \
DOCS_TOKEN="<oauth token>" \
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_doc.py" \
  --spec docs/handover/specs/<tab>.json --doc <docId>
```

`SSL_CERT_FILE` guards the macOS python.org `CERTIFICATE_VERIFY_FAILED` case; harmless
elsewhere.
