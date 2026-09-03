#!/usr/bin/env python3
"""
The anti-hallucination control. Nothing reaches the user unvalidated.

Every rule below is blocking: one violation and this exits non-zero. The skill
must not present a finding this rejects, and must not route around a rejection
by weakening the citation or deleting the evidence. A finding that cannot be
substantiated does not get shown.

SCOPE LIMIT, stated plainly: this validates CODE-SIDE findings, where a file and
a line exist to check against. Findings derived from a listing screenshot cannot
be validated mechanically — there is no artefact on disk to re-read. Those rely
on two rules in SKILL.md instead: refuse to score a field that is not legible,
and quote the value actually read.

Usage:
  python3 validate-findings.py [--findings FILE] [--path ROOT] [--final]
  python3 validate-findings.py --self-test
"""

import argparse
import json
import os
import re
import sys

SEVERITIES = ("BLOCKER", "HIGH", "MED", "LOW")
STAGES = ("scanned", "ready")
EVIDENCE_TYPES = ("file", "absence", "search")
MIN_QUOTE_CHARS = 25


def norm(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def read_lines(path):
    try:
        with open(path, "r", errors="ignore") as fh:
            return fh.read().splitlines()
    except OSError:
        return None


class Report:
    def __init__(self):
        self.violations = []
        self.warnings = []

    def fail(self, fid, message):
        self.violations.append((fid, message))

    def warn(self, fid, message):
        self.warnings.append((fid, message))


def validate_file_evidence(root, fid, ev, rep):
    path = ev.get("path")
    if not path:
        rep.fail(fid, "file evidence has no path")
        return

    full = os.path.normpath(os.path.join(root, path))
    if not full.startswith(os.path.normpath(root) + os.sep) and full != os.path.normpath(root):
        rep.fail(fid, f'evidence path "{path}" escapes the project root')
        return
    if not os.path.isfile(full):
        rep.fail(fid, f'evidence cites "{path}" but no such file exists — never '
                      f'reconstruct a plausible path from a naming convention')
        return

    line_no = ev.get("line")
    if not isinstance(line_no, int):
        rep.fail(fid, f'evidence for "{path}" has no integer line number')
        return

    lines = read_lines(full)
    if lines is None:
        rep.fail(fid, f'evidence cites "{path}" but it could not be read')
        return
    if line_no < 1 or line_no > len(lines):
        rep.fail(fid, f'evidence cites "{path}:{line_no}" but that file has '
                      f'{len(lines)} lines')
        return

    actual = lines[line_no - 1]

    # Ordering matters. `excerpt contains actual.strip()` is trivially true when
    # the cited line is blank, because every string contains the empty string.
    # So a citation that drifted onto an empty line — exactly what an edit above
    # it does — would satisfy the excerpt check and pass silently. Emptiness has
    # to be rejected before the match is attempted, not after.
    if not actual.strip():
        rep.fail(fid, f'evidence cites "{path}:{line_no}" but that line is blank — an '
                      f'empty line cannot support a finding, and is the signature of a '
                      f'line number left behind by an edit above it')
        return

    excerpt = ev.get("excerpt")
    if not norm(excerpt):
        rep.fail(fid, f'evidence for "{path}:{line_no}" has no excerpt, so the citation '
                      f'cannot be checked against the file')
        return

    a, e = norm(actual), norm(excerpt)
    if not (a in e or e in a):
        rep.fail(fid, f'evidence excerpt for "{path}:{line_no}" does not match the file.\n'
                      f'      cited: {e[:120]}\n'
                      f'      file:  {a[:120]}')


def validate_absence_evidence(root, fid, ev, rep):
    paths = ev.get("paths")
    if not isinstance(paths, list) or not paths:
        rep.fail(fid, "absence evidence lists no paths")
        return
    # Verified exactly as strictly as a file citation, just inverted: every
    # listed path must genuinely NOT resolve.
    present = [p for p in paths if os.path.exists(os.path.join(root, p))]
    if present:
        rep.fail(fid, f'absence evidence claims these paths do not exist, but they do: '
                      f'{", ".join(present)}')


def validate_search_evidence(root, fid, ev, rep):
    patterns = ev.get("patterns")
    if not isinstance(patterns, list) or not patterns:
        rep.fail(fid, "search evidence lists no patterns")
        return
    if ev.get("hits") != 0:
        rep.fail(fid, f'search evidence records hits={ev.get("hits")}; only a zero-hit '
                      f'search is usable as evidence of absence')
        return

    exts = tuple(ev.get("extensions") or ())
    if not exts:
        rep.fail(fid, "search evidence does not say which file extensions were scanned, "
                      "so the search cannot be repeated")
        return

    skip = ("/Pods/", "/node_modules/", "/build/", "/DerivedData/", "/.git/",
            "/vendor/", "/.gradle/", "/Carthage/", "/.check-appstore-details/")
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if not any(s in (os.path.join(dirpath, d) + "/") for s in skip)]
        for name in filenames:
            if not name.endswith(exts):
                continue
            full = os.path.join(dirpath, name)
            if any(s in full + "/" for s in skip):
                continue
            try:
                with open(full, "r", errors="ignore") as fh:
                    text = fh.read()
            except OSError:
                continue
            for pat in patterns:
                if pat in text:
                    found.append(f'{os.path.relpath(full, root)} contains "{pat}"')
                    break
            if found:
                break
        if found:
            break

    if found:
        rep.fail(fid, f'search evidence claims zero hits, but the search finds one: '
                      f'{found[0]} — re-run the scan, the tree has changed')


def validate(payload, root, final, rep):
    findings = payload.get("findings")
    if findings is None:
        rep.fail("-", "payload has no findings array")
        return

    seen_ids = set()
    for f in findings:
        fid = f.get("id") or "<no id>"
        if fid in seen_ids:
            rep.fail(fid, "duplicate finding id")
        seen_ids.add(fid)

        for field in ("title", "impact", "category", "fixLocation"):
            if not norm(f.get(field)):
                rep.fail(fid, f'"{field}" is empty')

        if f.get("severity") not in SEVERITIES:
            rep.fail(fid, f'severity "{f.get("severity")}" is not one of '
                          f'{", ".join(SEVERITIES)}')

        stage = f.get("stage")
        if stage not in STAGES:
            rep.fail(fid, f'stage "{stage}" is not one of {", ".join(STAGES)}')

        evidence = f.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            rep.fail(fid, "no evidence — if you cannot cite a location, the finding does "
                          "not get reported")
            continue

        for ev in evidence:
            etype = ev.get("type")
            if etype not in EVIDENCE_TYPES:
                rep.fail(fid, f'evidence type "{etype}" is not one of '
                              f'{", ".join(EVIDENCE_TYPES)}')
            elif etype == "file":
                validate_file_evidence(root, fid, ev, rep)
            elif etype == "absence":
                validate_absence_evidence(root, fid, ev, rep)
            elif etype == "search":
                validate_search_evidence(root, fid, ev, rep)

        # A policy citation is what separates a real requirement from an invented
        # one. It is required to present a finding, not to record it.
        policy = f.get("policy")
        if stage == "ready":
            if not isinstance(policy, dict):
                rep.fail(fid, "stage is ready but there is no policy citation — every "
                              "presented finding needs a guideline reference and a quote "
                              "from the policy fetched this run")
            else:
                if not norm(policy.get("guideline")):
                    rep.fail(fid, "policy citation has no guideline reference")
                if len(norm(policy.get("quote"))) < MIN_QUOTE_CHARS:
                    rep.fail(fid, f'policy quote is missing or too short to be a real '
                                  f'quotation (min {MIN_QUOTE_CHARS} characters)')
                if not norm(policy.get("source")):
                    rep.fail(fid, "policy citation has no source URL")
        elif final:
            rep.fail(fid, "still at stage \"scanned\" — add the policy citation and set "
                          "stage to \"ready\" before presenting it")
        else:
            rep.warn(fid, "stage \"scanned\": not presentable until a policy citation is "
                          "added and stage becomes \"ready\"")


# ── self-test ───────────────────────────────────────────────────────────────

def self_test():
    """
    Each case must be REJECTED. Run this after touching any rule above; if a
    case stops failing, the rule it covers has stopped working.
    """
    import tempfile

    root = tempfile.mkdtemp(prefix="cad-selftest-")
    real = os.path.join(root, "real.ts")
    with open(real, "w") as fh:
        fh.write("const a = 1;\n\nconst b = 2;\n")   # line 2 is deliberately blank

    def finding(**over):
        base = {
            "id": "T-001", "stage": "scanned", "category": "test", "severity": "MED",
            "title": "t", "impact": "i", "fixLocation": "code", "policy": None,
            "evidence": [],
        }
        base.update(over)
        return {"findings": [base]}

    cases = [
        ("path that does not exist",
         finding(evidence=[{"type": "file", "path": "nope.ts", "line": 1,
                            "excerpt": "const a = 1;"}])),
        ("line past end of file",
         finding(evidence=[{"type": "file", "path": "real.ts", "line": 99,
                            "excerpt": "const a = 1;"}])),
        ("citation landing on a blank line",
         finding(evidence=[{"type": "file", "path": "real.ts", "line": 2,
                            "excerpt": "const a = 1;"}])),
        ("excerpt disagreeing with the file",
         finding(evidence=[{"type": "file", "path": "real.ts", "line": 1,
                            "excerpt": "something else entirely"}])),
        ("absence claim whose path does exist",
         finding(evidence=[{"type": "absence", "paths": ["real.ts"]}])),
        ("zero-hit search that actually hits",
         finding(evidence=[{"type": "search", "patterns": ["const a"],
                            "extensions": [".ts"], "hits": 0}])),
        ("severity outside the set",
         finding(severity="CRITICAL",
                 evidence=[{"type": "file", "path": "real.ts", "line": 1,
                            "excerpt": "const a = 1;"}])),
        ("no evidence at all", finding(evidence=[])),
        ("ready without a policy citation",
         finding(stage="ready",
                 evidence=[{"type": "file", "path": "real.ts", "line": 1,
                            "excerpt": "const a = 1;"}])),
        ("ready with a too-short quote",
         finding(stage="ready",
                 policy={"guideline": "2.1", "quote": "short", "source": "https://x"},
                 evidence=[{"type": "file", "path": "real.ts", "line": 1,
                            "excerpt": "const a = 1;"}])),
    ]

    passing = finding(
        stage="ready",
        policy={"guideline": "2.3 Accurate Metadata",
                "quote": "Make sure your app description, screenshots, and previews "
                         "accurately reflect the app's core experience",
                "source": "https://developer.apple.com/app-store/review/guidelines/"},
        evidence=[{"type": "file", "path": "real.ts", "line": 1,
                   "excerpt": "const a = 1;"}])

    failures = []
    for label, payload in cases:
        rep = Report()
        validate(payload, root, False, rep)
        if not rep.violations:
            failures.append(f"NOT REJECTED (rule is broken): {label}")
        else:
            print(f"  rejected  {label}")
            print(f"            -> {rep.violations[0][1].splitlines()[0][:100]}")

    rep = Report()
    validate(passing, root, True, rep)
    if rep.violations:
        failures.append(f"valid finding was rejected: {rep.violations[0][1]}")
    else:
        print("  accepted  a fully substantiated finding")

    print()
    if failures:
        for msg in failures:
            print(f"SELF-TEST FAILURE: {msg}")
        return 1
    print(f"self-test passed: {len(cases)} bad findings rejected, 1 good finding accepted")
    return 0


# ── main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Blocking evidence validator.")
    ap.add_argument("--findings", default=None,
                    help="findings.json (default: ./.check-appstore-details/findings.json)")
    ap.add_argument("--path", default=None,
                    help="project root (default: taken from the findings file)")
    ap.add_argument("--final", action="store_true",
                    help="require every finding to be stage \"ready\" with a policy citation")
    ap.add_argument("--self-test", dest="selftest", action="store_true",
                    help="verify the rules still reject known-bad findings")
    args = ap.parse_args()

    if args.selftest:
        return self_test()

    findings_path = args.findings or os.path.join(
        os.getcwd(), ".check-appstore-details", "findings.json")
    if not os.path.isfile(findings_path):
        print(f"validate-findings: no findings file at {findings_path}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(open(findings_path).read())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"validate-findings: cannot parse {findings_path}: {exc}", file=sys.stderr)
        return 2

    root = args.path or (payload.get("scan") or {}).get("path") or os.getcwd()
    root = os.path.abspath(os.path.expanduser(root))

    rep = Report()
    validate(payload, root, args.final, rep)

    total = len(payload.get("findings") or [])
    if rep.violations:
        print(f"validate-findings: {len(rep.violations)} evidence validation "
              f"failure(s) across {total} finding(s). NOTHING may be presented until "
              f"these are fixed.\n")
        for fid, message in rep.violations:
            print(f"  {fid}: {message}")
        print("\nEvery finding must cite a real file:line, a genuinely absent path, or a "
              "genuinely empty search.\nDo not weaken a citation to get past this — drop "
              "the finding instead.")
        return 1

    print(f"validate-findings: {total} finding(s) validated.")
    for fid, message in rep.warnings:
        print(f"  note {fid}: {message}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
