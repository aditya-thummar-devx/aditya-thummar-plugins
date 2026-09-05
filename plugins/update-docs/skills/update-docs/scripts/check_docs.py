#!/usr/bin/env python3
"""
Docs verifier for update-docs.

Checks a docs tree for the four failures that make a docs restructure quietly
wrong: a relative link to a file that does not exist, a link to a heading anchor
that does not exist, a doc missing front-matter, and a stray reference to an old
path that was supposed to be gone (e.g. a `legacy/` holding dir after a move).

Read-only. Prints findings grouped by kind and exits non-zero if any hard
failure (broken link or anchor) is found. Missing front-matter and stale-path
references are reported as warnings by default; --strict makes them fail too.

Usage:
  python3 check_docs.py <docs-dir> [--stale-path legacy] [--strict]
"""

import argparse
import os
import re
import sys

LINK_RE = re.compile(r"\]\((\.[^)#]+\.md[a-z]*)(#([^)]+))?\)")   # relative .md/.mdx links
SELF_ANCHOR_RE = re.compile(r"\]\((#[^)]+)\)")                    # same-file #anchor links
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*$")


def slug(text):
    """GitHub-style heading anchor slug: lower, drop punctuation/emoji, spaces->'-'."""
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return s.replace(" ", "-")


def md_files(root):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not d.startswith(".") and d != "node_modules"]
        for name in fn:
            if name.lower().endswith((".md", ".mdx")):
                yield os.path.join(dp, name)


def heading_slugs(path, cache):
    key = os.path.normpath(path)
    if key not in cache:
        slugs = []
        try:
            with open(path, "r", errors="ignore") as fh:
                for line in fh:
                    m = HEADING_RE.match(line)
                    if m:
                        slugs.append(slug(m.group(2)))
        except OSError:
            pass
        cache[key] = slugs
    return cache[key]


def main():
    ap = argparse.ArgumentParser(description="Docs verifier for update-docs.")
    ap.add_argument("docs_dir", help="directory to check (e.g. docs/)")
    ap.add_argument("--stale-path", default=None,
                    help="report links whose target contains this substring (e.g. 'legacy')")
    ap.add_argument("--strict", action="store_true",
                    help="treat missing front-matter and stale refs as failures too")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.docs_dir))
    if not os.path.isdir(root):
        print(f"check_docs: not a directory: {root}", file=sys.stderr)
        return 2

    files = sorted(md_files(root))
    cache = {}
    broken_links, broken_anchors, missing_fm, stale = [], [], [], []

    for f in files:
        text = open(f, "r", errors="ignore").read()
        rel_f = os.path.relpath(f, root)
        d = os.path.dirname(f)

        if not text.startswith("---\n"):
            missing_fm.append(rel_f)

        for m in LINK_RE.finditer(text):
            target, anchor = m.group(1), m.group(3)
            tgt = os.path.normpath(os.path.join(d, target))
            if not os.path.exists(tgt):
                broken_links.append(f"{rel_f} -> {target}")
                continue
            if anchor and anchor not in heading_slugs(tgt, cache):
                broken_anchors.append(f"{rel_f} -> {target}#{anchor}")

        for m in SELF_ANCHOR_RE.finditer(text):
            a = m.group(1)[1:]
            if a not in heading_slugs(f, cache):
                broken_anchors.append(f"{rel_f} -> {m.group(1)}")

        if args.stale_path:
            for m in re.finditer(r"\]\(([^)]*" + re.escape(args.stale_path) + r"[^)]*)\)", text):
                stale.append(f"{rel_f} -> {m.group(1)}")

    def report(title, items):
        if items:
            print(f"\n{title} ({len(items)}):")
            for i in items:
                print(f"  {i}")

    report("BROKEN LINKS", broken_links)
    report("BROKEN ANCHORS", broken_anchors)
    report("MISSING FRONT-MATTER", missing_fm)
    if args.stale_path:
        report(f"STALE '{args.stale_path}' REFERENCES", stale)

    hard = len(broken_links) + len(broken_anchors)
    soft = len(missing_fm) + len(stale)
    print(f"\ndocs: {len(files)} | broken links: {len(broken_links)} | "
          f"broken anchors: {len(broken_anchors)} | missing front-matter: {len(missing_fm)}"
          + (f" | stale refs: {len(stale)}" if args.stale_path else ""))

    if hard or (args.strict and soft):
        print("RESULT: FAIL")
        return 1
    print("RESULT: OK" + (" (with warnings)" if soft else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
