#!/usr/bin/env python3
"""
Content spec -> new Google Doc tab (run-and-verify, stdlib only).

Adds ONE new tab (always created fresh, at the end) to a Google Doc and fills it
from a content SPEC. Used by the prepare-handover-docs skills to build each tab of
a mobile-app handover document. Project-agnostic: the engine only consumes the spec.

DESIGN
  - Each tab is described by a content SPEC (JSON, see references/spec-format.md).
    This engine is stable; only the spec changes per run.
  - Tab creation: Docs API `addDocumentTab`. Content: one `insertText` of the whole
    buffer at index 1 of the tab segment, then style/bullet/indent/link requests by
    offsets computed from that buffer (post-insert coordinate space).
  - Images: uploaded to Drive, made link-readable for the seconds it takes Google to
    fetch them into the doc, inserted via `insertInlineImage`, then DELETED. Bytes end
    up embedded; the public window is momentary (safe for confidential images).
  - Verify: re-fetch the tab and assert every block's text landed. Loop lives in the
    skill: on FAIL, fix the spec and re-run (tabs are always new, so no dedupe needed).

AUTH
  Set env DOCS_TOKEN to an OAuth access token with scopes:
    https://www.googleapis.com/auth/documents
    https://www.googleapis.com/auth/drive        (only needed when the spec has images)
  Any source works (user login or service-account minted token) — the engine only
  needs the bearer string.

USAGE
  python3 build_doc.py --spec example --dry-run          # prints requests + self-check, no network
  python3 build_doc.py --spec env-details.json           # live: create tab, build, verify
  python3 build_doc.py --spec s.json --doc <id> --tab "Env Details"   # override docId/title

TLS NOTE
  Some Python installs (e.g. python.org builds on macOS) ship no CA bundle for
  urllib, giving CERTIFICATE_VERIFY_FAILED. Run with a bundle, e.g.:
    SSL_CERT_FILE="$(python3 -m certifi 2>/dev/null || echo /etc/ssl/cert.pem)" \
      python3 build_doc.py --spec s.json --doc <id>
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

DOCS = "https://docs.googleapis.com/v1/documents"
DRIVE = "https://www.googleapis.com/upload/drive/v3/files"
DRIVE_META = "https://www.googleapis.com/drive/v3/files"

# ---- style tokens (Google Sans throughout, black) ----
BODY_FONT = "Google Sans"
HEAD_FONT = "Google Sans"
BLACK = {"red": 0.0, "green": 0.0, "blue": 0.0}
LINK = {"red": 0.0667, "green": 0.333, "blue": 0.8}  # #1155CC
DETAIL_INDENT_PT = 72.0   # tab-indented detail lines
BULLET_INDENT_PT = 18.0   # per nesting level
IMAGE_TARGET_HEIGHT_PT = 280.0  # ~1/3 of an A4 page height (841.9pt); images sized by height
IMAGE_MAX_WIDTH_PT = 451.0      # content width (A4 minus 1in margins) — cap for wide images
ONE_LINE_SPACE_PT = 18.0        # one-line gap above every bold title (heading, label, field key)


# ============================================================ spec -> buffer + requests
def assemble(spec):
    """Return (text_buffer, style_requests, image_ops). Offsets are in the tab segment
    coordinate space assuming the buffer is inserted at index 1."""
    buf = []           # list of str pieces (each block contributes text + "\n")
    pos = 0            # running length in buffer
    reqs = []          # style/paragraph/bullet requests (no char changes)
    images = []        # {"absIndex": int, "path": str}
    bullet_ranges = [] # (startAbs, endAbs) to bullet after text exists
    tabs_before = 0    # leading tabs emitted so far — createParagraphBullets strips them
                       # in the text batch, so image indices (inserted in a later batch)
                       # must be shifted left by the count of tabs before them.
    cur_level = 0      # nesting level of the most recent bullet, so a field's detail
                       # lines indent under it.

    def emit(text):
        nonlocal pos
        start = pos
        buf.append(text + "\n")
        pos += len(text) + 1
        return start, start + len(text)  # [textStart, textEnd) within buffer

    def abs_(p):
        return 1 + p  # buffer offset -> tab segment index

    for b in spec["blocks"]:
        t = b.get("type")

        if t == "spacer":
            buf.append("\n")           # a blank line (no style, no bullet) — visible one-line gap
            pos += 1
            continue

        if t == "image":
            start = pos
            buf.append("\n")           # placeholder empty line (holds the image)
            pos += 1
            images.append({"absIndex": abs_(start) - tabs_before, "path": b["path"],
                           "size_pt": b.get("size_pt")})
            # one-line gap above and below the image (main-batch coord space, pre tab-strip)
            reqs.append(_para_style(abs_(start), abs_(start) + 1,
                                    space_above=ONE_LINE_SPACE_PT, space_below=ONE_LINE_SPACE_PT))
            continue

        text = b.get("text", "")
        s, e = emit(text)
        pstart, pend = abs_(s), abs_(s) + len(text) + 1  # include newline for paragraph style

        if t in ("h1", "h2", "comp"):
            named = {"h1": "HEADING_1", "h2": "HEADING_2", "comp": "HEADING_3"}[t]
            reqs.append(_para_style(pstart, pend, named_style=named, space_above=ONE_LINE_SPACE_PT))
            reqs.append(_text_style(abs_(s), abs_(e), bold=True, font=HEAD_FONT, color=BLACK))

        elif t == "label":
            reqs.append(_para_style(pstart, pend, space_above=ONE_LINE_SPACE_PT))
            reqs.append(_text_style(abs_(s), abs_(e), bold=True, font=HEAD_FONT, color=BLACK))

        elif t == "para":
            reqs.append(_text_style(abs_(s), abs_(e), bold=False, font=BODY_FONT, color=BLACK))

        elif t == "bullet":
            # Google Docs derives a bullet's nesting level from the number of leading
            # TAB chars, so we prefix `level` tabs; createParagraphBullets removes them.
            level = int(b.get("level", 0))
            cur_level = level
            if level:
                shown = ("\t" * level) + text
                buf[-1] = shown + "\n"
                pos = s + len(shown) + 1
                vis_s, vis_e = s + level, s + len(shown)
                pstart, pend = abs_(s), abs_(s) + len(shown) + 1
                tabs_before += level
            else:
                vis_s, vis_e = s, e
            reqs.append(_text_style(abs_(vis_s), abs_(vis_e), bold=bool(b.get("bold", False)), font=BODY_FONT, color=BLACK))
            sa = ONE_LINE_SPACE_PT if (b.get("bold") or b.get("space")) else None
            sb = ONE_LINE_SPACE_PT if b.get("space_below") else None
            if sa is not None or sb is not None:   # one-line gap above bold titles; below flagged bullets
                reqs.append(_para_style(pstart, pend, space_above=sa, space_below=sb))
            bullet_ranges.append((pstart, pend))

        elif t == "detail":
            # Indent one notch deeper than the parent field's bullet (bullets land at
            # 36pt per nesting level), so detail lines nest under the field at any depth.
            detail_indent = BULLET_INDENT_PT * 2 * (cur_level + 1) + BULLET_INDENT_PT
            reqs.append(_para_style(pstart, pend, indent_start=detail_indent))
            reqs.append(_text_style(abs_(s), abs_(e), bold=bool(b.get("bold", False)), font=BODY_FONT, color=BLACK))

        elif t == "figlink":
            # renders "[<text>]" as a hyperlink
            shown = "[" + b["text"] + "]"
            buf[-1] = shown + "\n"
            pos = s + len(shown) + 1
            reqs.append(_text_style(abs_(s), abs_(s) + len(shown), font=BODY_FONT, color=LINK,
                                    link=b.get("url")))

        elif t == "figline":
            # "<prefix> [<text>]" with the bracket part linked
            prefix = b.get("prefix", "Link:")
            shown = prefix + " [" + b["text"] + "]"
            buf[-1] = shown + "\n"
            pos = s + len(shown) + 1
            reqs.append(_text_style(abs_(s), abs_(s) + len(shown), font=BODY_FONT, color=BLACK))
            ls = s + len(prefix) + 1
            reqs.append(_text_style(abs_(ls), abs_(s) + len(shown), color=LINK, link=b.get("url")))

        else:
            raise ValueError("unknown block type: %r" % t)

    # bullets applied last, back-to-front: createParagraphBullets strips the leading
    # tabs (shifting later indices), so highest-index ranges must be processed first.
    for (ps, pe) in sorted(bullet_ranges, key=lambda r: r[0], reverse=True):
        reqs.append({
            "createParagraphBullets": {
                "range": _range(ps, pe),
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        })

    return "".join(buf), reqs, images


def _range(start, end, tab_id=None):
    r = {"startIndex": start, "endIndex": end}
    if tab_id:
        r["tabId"] = tab_id
    return r


def _para_style(start, end, named_style=None, indent_start=None, space_above=None, space_below=None):
    style, fields = {}, []
    if named_style:
        style["namedStyleType"] = named_style
        fields.append("namedStyleType")
    if indent_start is not None:
        style["indentStart"] = {"magnitude": indent_start, "unit": "PT"}
        style["indentFirstLine"] = {"magnitude": indent_start, "unit": "PT"}
        fields += ["indentStart", "indentFirstLine"]
    if space_above is not None:
        style["spaceAbove"] = {"magnitude": space_above, "unit": "PT"}
        fields.append("spaceAbove")
    if space_below is not None:
        style["spaceBelow"] = {"magnitude": space_below, "unit": "PT"}
        fields.append("spaceBelow")
    return {"updateParagraphStyle": {"range": _range(start, end), "paragraphStyle": style,
                                     "fields": ",".join(fields)}}


def _text_style(start, end, bold=None, font=None, color=None, link=None):
    style, fields = {}, []
    if bold is not None:
        style["bold"] = bold
        fields.append("bold")
    if font is not None:
        style["weightedFontFamily"] = {"fontFamily": font}
        fields.append("weightedFontFamily")
    if color is not None:
        style["foregroundColor"] = {"color": {"rgbColor": color}}
        fields.append("foregroundColor")
    if link is not None:
        style["link"] = {"url": link}
        fields.append("link")
    return {"updateTextStyle": {"range": _range(start, end), "textStyle": style,
                                "fields": ",".join(fields)}}


def _tabify(reqs, tab_id):
    """Attach tabId to every range so requests target the new tab segment."""
    for r in reqs:
        body = next(iter(r.values()))
        if "range" in body:
            body["range"]["tabId"] = tab_id
    return reqs


# ============================================================ self-check (dry-run)
def self_check(text, reqs, images):
    n = len(text)
    hi = 1 + n
    for r in reqs:
        body = next(iter(r.values()))
        rng = body.get("range")
        if rng:
            assert 1 <= rng["startIndex"] < rng["endIndex"] <= hi, ("range out of bounds", rng, hi)
    for im in images:
        assert 1 <= im["absIndex"] <= hi, ("image index out of bounds", im, hi)
    return True


# ============================================================ HTTP (stdlib)
def _token():
    tok = os.environ.get("DOCS_TOKEN")
    if not tok:
        sys.exit("DOCS_TOKEN env not set (OAuth access token with documents[+drive] scope).")
    return tok


def _req(url, method="GET", body=None, headers=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    h = {"Authorization": "Bearer " + _token()}
    if data is not None and raw is None:
        h["Content-Type"] = ctype
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as ex:
        sys.exit("HTTP %s on %s\n%s" % (ex.code, url, ex.read().decode()))


def add_tab(doc_id, title):
    before = _req("%s/%s?includeTabsContent=true" % (DOCS, doc_id))
    index = len(before.get("tabs", []))
    _req("%s/%s:batchUpdate" % (DOCS, doc_id), "POST",
         {"requests": [{"addDocumentTab": {"tabProperties": {"index": index, "title": title}}}]})
    after = _req("%s/%s?includeTabsContent=true" % (DOCS, doc_id))
    tabs = after.get("tabs", [])
    return tabs[-1]["tabProperties"]["tabId"]


def upload_image(path):
    with open(path, "rb") as f:
        raw = f.read()
    mime = "image/png" if path.lower().endswith("png") else "image/jpeg"
    meta = _req(DRIVE + "?uploadType=media&fields=id", "POST", raw=raw, headers={"Content-Type": mime})
    fid = meta["id"]
    _req("%s/%s/permissions" % (DRIVE_META, fid), "POST", {"type": "anyone", "role": "reader"})
    return fid, "https://drive.google.com/uc?export=view&id=" + fid


def delete_file(fid):
    _req("%s/%s" % (DRIVE_META, fid), "DELETE")


def _png_size(path):
    """(width, height) in px for a PNG, else None (e.g. jpeg)."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    import struct
    return struct.unpack(">II", head[16:24])


def _image_object_size(path):
    """Size the image to IMAGE_TARGET_HEIGHT_PT (1/3 page), preserving aspect ratio;
    cap width at IMAGE_MAX_WIDTH_PT for wide/landscape images."""
    size = _png_size(path)
    if not size:
        return {"width": {"magnitude": 460, "unit": "PT"}}  # fallback (unknown dims)
    w, h = size
    th = IMAGE_TARGET_HEIGHT_PT
    tw = th * (w / h)
    if tw > IMAGE_MAX_WIDTH_PT:
        tw = IMAGE_MAX_WIDTH_PT
        th = tw * (h / w)
    return {"height": {"magnitude": th, "unit": "PT"}, "width": {"magnitude": tw, "unit": "PT"}}


def _spec_object_size(im):
    """Honor an explicit spec size ({"size_pt": {"width":W,"height":H}}) when present
    (e.g. an image resized by hand in the doc); otherwise auto-size by height."""
    sp = im.get("size_pt")
    if sp and sp.get("width") and sp.get("height"):
        return {"height": {"magnitude": sp["height"], "unit": "PT"},
                "width": {"magnitude": sp["width"], "unit": "PT"}}
    return _image_object_size(im["path"])


def insert_images(doc_id, tab_id, images):
    # back-to-front so earlier indices stay valid as inserts shift the tail
    tmp = []
    for im in sorted(images, key=lambda x: x["absIndex"], reverse=True):
        fid, url = upload_image(im["path"])
        tmp.append(fid)
        _req("%s/%s:batchUpdate" % (DOCS, doc_id), "POST", {"requests": [{
            "insertInlineImage": {
                "location": {"index": im["absIndex"], "tabId": tab_id},
                "uri": url,
                "objectSize": _spec_object_size(im),
            }
        }]})
        time.sleep(0.5)
    for fid in tmp:
        try:
            delete_file(fid)
        except SystemExit:
            pass  # leave temp file if delete fails; content is already embedded


def verify(doc_id, tab_id, spec):
    doc = _req("%s/%s?includeTabsContent=true" % (DOCS, doc_id))
    tab = next((t for t in doc.get("tabs", []) if t["tabProperties"]["tabId"] == tab_id), None)
    got = _collect_text(tab["documentTab"]["body"]["content"]) if tab else ""
    missing = []
    for b in spec["blocks"]:
        txt = (b.get("text") or "").strip()
        if txt and txt[:24] not in got:
            missing.append(txt[:40])
    return missing


def _collect_text(content):
    out = []
    for el in content:
        for e in (el.get("paragraph", {}) or {}).get("elements", []):
            out.append((e.get("textRun") or {}).get("content", ""))
    return "".join(out)


# ============================================================ main
def run(spec, dry_run):
    text, reqs, images = assemble(spec)
    self_check(text, reqs, images)

    if dry_run:
        print("=== buffer (%d chars) ===" % len(text))
        print(text)
        print("=== %d style requests, %d images ===" % (len(reqs), len(images)))
        print(json.dumps(reqs[:6], indent=2))
        print("... self-check PASSED (all ranges in bounds)")
        return

    doc_id = spec["docId"]
    tab_id = add_tab(doc_id, spec["tabTitle"])
    _tabify(reqs, tab_id)
    _req("%s/%s:batchUpdate" % (DOCS, doc_id), "POST", {"requests": [
        {"insertText": {"location": {"index": 1, "tabId": tab_id}, "text": text}}
    ] + reqs})
    if images:
        insert_images(doc_id, tab_id, images)

    missing = verify(doc_id, tab_id, spec)
    if missing:
        print("VERIFY FAIL — missing text:\n  " + "\n  ".join(missing))
        sys.exit(2)
    print("OK — tab '%s' created (%s), %d blocks, %d images, verified." %
          (spec["tabTitle"], tab_id, len(spec["blocks"]), len(images)))


EXAMPLE = {
    "docId": "REPLACE_DOC_ID",
    "tabTitle": "Env Details",
    "blocks": [
        {"type": "h1", "text": "Environment Configuration"},
        {"type": "para", "text": "One-line summary of how this app reads its runtime configuration."},
        {"type": "label", "text": "Environment files"},
        {"type": "bullet", "text": ".env — production build", "level": 0},
        {"type": "bullet", "text": ".env.staging — staging build", "level": 0},
        {"type": "label", "text": "Download the filled files"},
        {"type": "figline", "prefix": "Handover folder:", "text": "https://drive.google.com/drive/folders/EXAMPLE",
         "url": "https://drive.google.com/drive/folders/EXAMPLE"},
        {"type": "label", "text": "What the env file contains"},
        {"type": "bullet", "text": "Endpoints & URLs", "level": 0},
        {"type": "bullet", "text": "API_BASE_URL — backend base URL.", "level": 1},
        {"type": "detail", "text": "Read from the redacted example file; values live only in the handover folder."},
        {"type": "bullet", "text": "Credentials (secrets — vault / folder only)", "level": 0},
        {"type": "bullet", "text": "API_TOKEN — bearer token. (credential)", "level": 1},
    ],
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="path to spec json, or 'example'")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--doc", help="override docId")
    ap.add_argument("--tab", help="override tabTitle")
    a = ap.parse_args()

    spec = dict(EXAMPLE) if a.spec == "example" else json.load(open(a.spec))
    if a.doc:
        spec["docId"] = a.doc
    if a.tab:
        spec["tabTitle"] = a.tab
    run(spec, a.dry_run)


if __name__ == "__main__":
    main()
