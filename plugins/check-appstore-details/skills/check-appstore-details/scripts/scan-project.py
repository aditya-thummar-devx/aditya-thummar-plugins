#!/usr/bin/env python3
"""
Deterministic project read for check-appstore-details.

Reads a mobile project and emits one findings.json describing what the code
actually declares and does. It never contacts Apple, never reads a credential,
and never edits the project it is pointed at.

Everything here must be reproducible: the same tree in the same state produces
the same output. Judgement calls (does this description claim a feature the app
lacks, is this territory list defensible) belong to the skill, not to this file.

Two rules this script exists to enforce mechanically:

  1. Version drift is found by comparing targets to EACH OTHER, never against a
     configured expected value. No baseline is ever stored, so the check works
     on a project it has never seen.

  2. Framework detection is dependency-driven, never file-presence-driven.
     `app.json` ships in bare React Native too, so its presence proves nothing.

Usage:
  python3 scan-project.py [--path DIR] [--out FILE] [--print]
"""

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
SIGNALS_PATH = os.path.join(HERE, "signals.json")

SKIP_PARTS = (
    os.sep + "Pods" + os.sep,
    os.sep + "node_modules" + os.sep,
    os.sep + "build" + os.sep,
    os.sep + "DerivedData" + os.sep,
    os.sep + ".git" + os.sep,
    os.sep + "vendor" + os.sep,
    os.sep + ".gradle" + os.sep,
    os.sep + "Carthage" + os.sep,
    os.sep + ".check-appstore-details" + os.sep,
)

SOURCE_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
               ".swift", ".m", ".mm", ".h", ".java", ".kt", ".dart")
MAX_SOURCE_BYTES = 2_000_000

SEVERITIES = ("BLOCKER", "HIGH", "MED", "LOW")


# ── plumbing ────────────────────────────────────────────────────────────────

def skipped(path):
    padded = path if path.endswith(os.sep) else path + os.sep
    return any(part in padded for part in SKIP_PARTS)


def read_text(path):
    try:
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def walk(root, match):
    """Yield absolute paths under root where match(basename) is true."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not skipped(os.path.join(dirpath, d))]
        for name in filenames:
            if match(name):
                full = os.path.join(dirpath, name)
                if not skipped(full):
                    yield full


def walk_dirs(root, match):
    for dirpath, dirnames, _ in os.walk(root):
        dirnames[:] = [d for d in dirnames if not skipped(os.path.join(dirpath, d))]
        for name in list(dirnames):
            if match(name):
                yield os.path.join(dirpath, name)


def git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ── provenance ──────────────────────────────────────────────────────────────

def scan_provenance(root):
    """What was actually read. A finding derived from a stale tree is wrong."""
    is_repo = bool(git(root, "rev-parse", "--is-inside-work-tree"))
    status = git(root, "status", "--porcelain") if is_repo else ""
    return {
        "path": root,
        "isGitRepo": is_repo,
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD") or None,
        "commit": git(root, "rev-parse", "--short", "HEAD") or None,
        "commitFull": git(root, "rev-parse", "HEAD") or None,
        "dirty": bool(status),
        "dirtyFileCount": len([l for l in status.splitlines() if l.strip()]),
        "scannedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ── framework ───────────────────────────────────────────────────────────────

def detect_framework(root):
    """
    Dependency-driven. The failure this avoids: treating the presence of
    app.json as proof of Expo. Bare React Native ships app.json, so a
    file-presence check reports both frameworks at once and is simply wrong.
    """
    deps = {}
    pkg_path = os.path.join(root, "package.json")
    if os.path.exists(pkg_path):
        try:
            pkg = json.loads(read_text(pkg_path) or "{}")
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        except json.JSONDecodeError:
            deps = {}

    framework, version, basis = None, None, None

    if "expo" in deps:
        framework, version = "expo", deps["expo"]
        basis = "package.json dependencies contain \"expo\""
    elif "react-native" in deps:
        framework, version = "react-native", deps["react-native"]
        basis = "package.json dependencies contain \"react-native\" and not \"expo\""
    elif any(k.startswith("@capacitor/") for k in deps):
        framework = "capacitor"
        basis = "package.json dependencies contain an @capacitor/* package"
    else:
        pubspec = os.path.join(root, "pubspec.yaml")
        if os.path.exists(pubspec) and re.search(r"^\s*flutter\s*:", read_text(pubspec), re.M):
            framework, basis = "flutter", "pubspec.yaml declares a flutter dependency"
        elif os.path.exists(os.path.join(root, "ProjectSettings", "ProjectSettings.asset")):
            framework, basis = "unity", "ProjectSettings/ProjectSettings.asset present"

    signals = load_signals()
    verified_list = signals["frameworkMarkers"]["verified"]

    if framework is None:
        if any(True for _ in walk_dirs(root, lambda n: n.endswith(".xcodeproj"))):
            framework, basis = "native-ios", "an .xcodeproj exists with no JS or Dart manifest"

    return {
        "framework": framework,
        "frameworkVersion": version,
        "detectionBasis": basis,
        "verified": framework in verified_list,
        "dependencyCount": len(deps),
        "dependencies": deps,
    }


def load_signals():
    return json.loads(read_text(SIGNALS_PATH) or "{}")


# ── pbxproj ─────────────────────────────────────────────────────────────────

def brace_end(text, open_idx):
    """Index of the '}' closing the '{' at open_idx, or -1."""
    depth = 0
    for i in range(open_idx, len(text)):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return -1


SETTING_RE_CACHE = {}


def setting(body, key, base_line=None):
    """
    Value of a build setting, plus the line it actually sits on.

    The line matters: a citation must point at the setting, not at the
    enclosing `buildSettings = {`. Pointing at the block is what the evidence
    validator rejects, and rightly — the excerpt would never match the file.
    """
    rx = SETTING_RE_CACHE.get(key)
    if rx is None:
        rx = re.compile(rf'^\s*{re.escape(key)}\s*=\s*(.+?);\s*$', re.M)
        SETTING_RE_CACHE[key] = rx
    m = rx.search(body)
    if not m:
        return (None, None, None) if base_line is not None else None

    val = m.group(1).strip()
    if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
        val = val[1:-1]
    val = val or None

    if base_line is None:
        return val
    # body begins immediately after the '{', so body offset 0 is on base_line.
    line = base_line + body.count("\n", 0, m.start())
    return val, line, m.group(0).strip()


def parse_pbxproj(pbx_path, root):
    """
    Extract one record per XCBuildConfiguration that carries a bundle id.

    Target identity is taken from the settings themselves (bundle id + display
    name + product name) rather than by resolving the XCConfigurationList
    graph. That is enough to tell an app from its extensions and from a second
    flavour, and it avoids a full pbxproj parser for no gain.
    """
    text = read_text(pbx_path)
    records = []
    for m in re.finditer(r"buildSettings\s*=\s*\{", text):
        open_idx = text.index("{", m.start())
        close_idx = brace_end(text, open_idx)
        if close_idx < 0:
            continue
        body = text[open_idx + 1:close_idx]
        base_line = text.count("\n", 0, open_idx) + 1
        rel = os.path.relpath(pbx_path, root)

        bundle_id, bundle_line, bundle_excerpt = setting(
            body, "PRODUCT_BUNDLE_IDENTIFIER", base_line)
        if not bundle_id:
            continue

        tail = text[close_idx:close_idx + 400]
        cfg = re.search(r"^\s*name\s*=\s*\"?([\w .-]+)\"?;", tail, re.M)

        record = {
            "configuration": cfg.group(1).strip() if cfg else None,
            "bundleId": bundle_id,
            "path": rel,
            "cite": {"PRODUCT_BUNDLE_IDENTIFIER":
                     {"line": bundle_line, "excerpt": bundle_excerpt}},
        }
        for key, field in (
            ("MARKETING_VERSION", "marketingVersion"),
            ("CURRENT_PROJECT_VERSION", "buildNumber"),
            ("INFOPLIST_KEY_CFBundleDisplayName", "displayName"),
            ("PRODUCT_NAME", "productName"),
            ("TARGETED_DEVICE_FAMILY", "deviceFamily"),
            ("IPHONEOS_DEPLOYMENT_TARGET", "deploymentTarget"),
        ):
            value, line, excerpt = setting(body, key, base_line)
            record[field] = value
            if value is not None:
                record["cite"][key] = {"line": line, "excerpt": excerpt}
        records.append(record)
    return records


def cite(target, key, note=None):
    """File evidence for one build setting on one target."""
    loc = (target.get("cite") or {}).get(key)
    if not loc:
        return None
    ev = {"type": "file", "path": target["path"],
          "line": loc["line"], "excerpt": loc["excerpt"]}
    if note:
        ev["note"] = note
    return ev


def classify_targets(records):
    """
    An extension is a bundle id that sits underneath another bundle id present
    in the same project. Deriving it this way needs no target-type lookup.
    """
    ids = {r["bundleId"] for r in records}
    for r in records:
        parents = [b for b in ids if b != r["bundleId"] and r["bundleId"].startswith(b + ".")]
        r["kind"] = "extension" if parents else "app"
        r["parentBundleId"] = sorted(parents, key=len)[-1] if parents else None
    return records


# ── plists ──────────────────────────────────────────────────────────────────

def load_plist(path):
    try:
        with open(path, "rb") as fh:
            return plistlib.load(fh)
    except Exception:
        return None


def find_line(path, needle):
    """1-indexed line of the first non-blank line containing needle."""
    for i, line in enumerate(read_text(path).splitlines(), start=1):
        if needle in line and line.strip():
            return i, line.strip()
    return None, None


def scan_info_plists(root):
    out = []
    for path in walk(root, lambda n: n == "Info.plist"):
        data = load_plist(path)
        if data is None:
            continue
        usage = {}
        for key, value in data.items():
            if key.startswith("NS") and key.endswith("UsageDescription"):
                line, excerpt = find_line(path, f"<key>{key}</key>")
                usage[key] = {
                    "text": value if isinstance(value, str) else None,
                    "line": line,
                    "excerpt": excerpt,
                }
        out.append({
            "path": os.path.relpath(path, root),
            "absPath": path,
            "usageDescriptions": usage,
            "backgroundModes": data.get("UIBackgroundModes") or [],
            "queriesSchemes": data.get("LSApplicationQueriesSchemes") or [],
            "usesNonExemptEncryption": data.get("ITSAppUsesNonExemptEncryption"),
            "urlSchemes": [s for t in (data.get("CFBundleURLTypes") or [])
                           for s in (t.get("CFBundleURLSchemes") or [])],
        })
    return out


def scan_privacy_manifests(root):
    out = []
    for path in walk(root, lambda n: n == "PrivacyInfo.xcprivacy"):
        data = load_plist(path)
        if data is None:
            continue
        tracking_line, tracking_excerpt = find_line(path, "<key>NSPrivacyTracking</key>")
        collected_line, collected_excerpt = find_line(
            path, "<key>NSPrivacyCollectedDataTypes</key>")
        collected = data.get("NSPrivacyCollectedDataTypes") or []
        out.append({
            "path": os.path.relpath(path, root),
            "tracking": bool(data.get("NSPrivacyTracking")),
            "trackingLine": tracking_line,
            "trackingExcerpt": tracking_excerpt,
            "collectedLine": collected_line,
            "collectedExcerpt": collected_excerpt,
            "collectedDataTypeCount": len(collected),
            "collectedDataTypes": [c.get("NSPrivacyCollectedDataType")
                                   for c in collected if isinstance(c, dict)],
            "trackingDomains": data.get("NSPrivacyTrackingDomains") or [],
            "accessedApiCategories": [
                a.get("NSPrivacyAccessedAPIType")
                for a in (data.get("NSPrivacyAccessedAPITypes") or [])
                if isinstance(a, dict)
            ],
        })
    return out


# ── android ─────────────────────────────────────────────────────────────────

def scan_android(root):
    out = []
    for path in walk(root, lambda n: n.startswith("build.gradle")):
        text = read_text(path)
        vn = re.search(r'versionName\s+"?([\w.\-]+)"?', text)
        vc = re.search(r"versionCode\s+(\d+)", text)
        app_id = re.search(r'applicationId\s+"([^"]+)"', text)
        if not (vn or vc):
            continue
        line = text.count("\n", 0, (vn or vc).start()) + 1
        out.append({
            "path": os.path.relpath(path, root),
            "versionName": vn.group(1) if vn else None,
            "versionCode": vc.group(1) if vc else None,
            "applicationId": app_id.group(1) if app_id else None,
            "line": line,
        })
    manifests = []
    for path in walk(root, lambda n: n == "AndroidManifest.xml"):
        text = read_text(path)
        perms = sorted(set(re.findall(r'android:name="(android\.permission\.[A-Z_]+)"', text)))
        if perms:
            manifests.append({"path": os.path.relpath(path, root), "permissions": perms})
    return {"gradle": out, "manifests": manifests}


# ── source index ────────────────────────────────────────────────────────────

def build_source_index(root):
    """Read every source file once. Later searches run over this, not the disk."""
    index = []
    for path in walk(root, lambda n: n.endswith(SOURCE_EXTS)):
        try:
            if os.path.getsize(path) > MAX_SOURCE_BYTES:
                continue
        except OSError:
            continue
        text = read_text(path)
        if text:
            index.append((os.path.relpath(path, root), text))
    return index


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _needle_regex(needle, case_sensitive):
    """
    Identifier-shaped needles match on word boundaries; anything else (package
    names, dotted calls, phrases) matches as a substring.

    Word boundaries are not cosmetic. A bare `startScan` substring match hits
    `startScanFromSheet` — a QR-code handler — and once produced two BLOCKER
    Bluetooth findings against an app with no Bluetooth code at all.
    """
    flags = 0 if case_sensitive else re.IGNORECASE
    if IDENTIFIER_RE.match(needle):
        return re.compile(rf"\b{re.escape(needle)}\b", flags)
    return re.compile(re.escape(needle), flags)


def search_index(index, needles, case_sensitive=True):
    """First hit per needle as file/line/excerpt evidence."""
    hits = []
    for needle in needles:
        rx = _needle_regex(needle, case_sensitive)
        for rel, text in index:
            m = rx.search(text)
            if not m:
                continue
            lines = text.splitlines()
            line_no = text.count("\n", 0, m.start()) + 1
            excerpt = lines[line_no - 1].strip() if line_no - 1 < len(lines) else ""
            if not excerpt:
                continue
            hits.append({"needle": needle, "path": rel, "line": line_no,
                         "excerpt": excerpt[:300]})
            break
    return hits


# ── signals ─────────────────────────────────────────────────────────────────

def detect_signals(root, deps, index, plists, signals):
    dep_names = set(deps)
    dep_blob = " ".join(dep_names).lower()

    def deps_matching(candidates):
        """
        Most specific candidate wins per dependency. Without this, a project
        depending only on react-native-fbsdk-next reports both that and
        react-native-fbsdk, because the shorter name is a prefix of the longer
        one. Two entries for one dependency reads as two SDKs.
        """
        cands = [c for c in candidates if not c.startswith("_")]
        found = set()
        for dep in dep_names:
            dl = dep.lower()
            matches = [c for c in cands if c.lower() == dl or c.lower() in dl]
            if matches:
                found.add(max(matches, key=len))
        return sorted(found)

    tracking = {
        bucket: deps_matching(items)
        for bucket, items in signals["trackingSdks"].items()
        if not bucket.startswith("_")
    }

    payments = {
        bucket: deps_matching(items)
        for bucket, items in signals["paymentSdks"].items()
        if not bucket.startswith("_")
    }

    scheme_pool = {s.lower() for p in plists for s in p["queriesSchemes"]}
    scheme_hits = {}
    for region, schemes in signals["paymentUrlSchemes"].items():
        if region.startswith("_"):
            continue
        matched = sorted(s for s in schemes if s.lower() in scheme_pool)
        if matched:
            scheme_hits[region] = matched

    # A bare three-letter match is far too loose: "Hong Kong SAR China" in a
    # country list is not the Saudi riyal, and a country picker will hand you a
    # dozen such false positives. Require the code to be a quoted token, or to
    # sit on a line that is talking about money.
    currency_ctx = re.compile(r"currenc|price|amount|money|payment|total|symbol|locale",
                              re.I)
    currency_hits = {}
    for code in signals["currencies"]:
        quoted = re.compile(rf"['\"`]{code}['\"`]")
        bare = re.compile(rf"\b{code}\b")
        for rel, text in index:
            lines = text.splitlines()
            for n, line in enumerate(lines, start=1):
                if quoted.search(line) or (bare.search(line) and currency_ctx.search(line)):
                    currency_hits.setdefault(code, {
                        "path": rel, "line": n, "excerpt": line.strip()[:200],
                    })
                    break
            if code in currency_hits:
                break

    postal = search_index(index, signals["postalValidators"]["fieldNames"], case_sensitive=False)

    logins = {}
    for kind, needles in signals["loginKinds"].items():
        if kind.startswith("_"):
            continue
        hits = search_index(index, needles)
        if hits:
            logins[kind] = hits[:4]

    return {
        "trackingSdks": tracking,
        "paymentSdks": payments,
        "paymentUrlSchemes": scheme_hits,
        "currencies": currency_hits,
        "postalValidators": postal[:6],
        "loginKinds": logins,
    }


def audit_permissions(index, plists, signals):
    """
    Both directions, with deliberately asymmetric strictness.

    "Declared but unused" searches strong AND weak needles, because a hit there
    SUPPRESSES a finding — being permissive is the conservative choice, and the
    cost of a false hit is only a missed low-severity report.

    "Used but undeclared" searches STRONG needles only, because a hit there
    CREATES a BLOCKER. A false positive at that severity is far more damaging
    than a miss, and destroys trust in every other finding alongside it.
    """
    table = {k: v for k, v in signals["permissionUsage"].items() if not k.startswith("_")}
    declared, unused, undeclared = {}, [], []

    all_declared = set()
    for p in plists:
        all_declared |= set(p["usageDescriptions"])

    for p in plists:
        for key, meta in p["usageDescriptions"].items():
            entry = table.get(key)
            strong = (entry or {}).get("strong", [])
            weak = (entry or {}).get("weak", [])
            hits = search_index(index, strong + weak) if entry else []
            declared[key] = {
                "plist": p["path"],
                "line": meta["line"],
                "excerpt": meta["excerpt"],
                "text": meta["text"],
                "knownSymbols": strong + weak,
                "usedAt": hits[:3],
                "used": bool(hits),
                "unknownKey": entry is None,
            }
            if entry and not hits:
                unused.append(key)

    for key, entry in table.items():
        if key in all_declared:
            continue
        strong = entry.get("strong", [])
        hits = search_index(index, strong)
        if hits:
            undeclared.append({"key": key, "usedAt": hits[:3], "matchedOn": "strong"})

    return {"declared": declared, "unused": unused, "undeclared": undeclared}


# ── findings ────────────────────────────────────────────────────────────────

class Findings:
    def __init__(self):
        self.items = []
        self.not_checked = []

    def add(self, category, severity, title, impact, fix_location, evidence,
            depends_on=None, note=None):
        assert severity in SEVERITIES, severity
        self.items.append({
            "id": f"CAD-{len(self.items) + 1:03d}",
            "stage": "scanned",
            "category": category,
            "severity": severity,
            "title": title,
            "impact": impact,
            "fixLocation": fix_location,
            "evidence": evidence,
            "policy": None,
            "dependsOn": depends_on or [],
            "note": note,
        })

    def skip(self, check, reason):
        self.not_checked.append({"check": check, "reason": reason})


def evaluate(root, project, targets, plists, manifests, android, sig, perms, toolchain, f):
    # ---- version alignment -------------------------------------------------
    versions = {}
    for t in targets:
        if t["marketingVersion"]:
            versions.setdefault(t["marketingVersion"], []).append(t)

    if len(versions) > 1:
        apps = {v for v, ts in versions.items() if any(t["kind"] == "app" for t in ts)}
        exts = {v for v, ts in versions.items() if any(t["kind"] == "extension" for t in ts)}
        cross = bool(apps and exts and apps != exts)
        ev = [e for ts in versions.values() for t in ts
              if (e := cite(t, "MARKETING_VERSION",
                            f'{t["kind"]} {t["bundleId"]} ({t["configuration"]})'))]
        f.add(
            "version",
            "BLOCKER" if cross else "HIGH",
            "MARKETING_VERSION disagrees across targets: " + ", ".join(sorted(versions)),
            ("An app extension whose CFBundleShortVersionString differs from the containing "
             "app fails upload validation outright, before review."
             if cross else
             "Targets disagree on the marketing version, so which value reaches the store "
             "depends on which scheme is archived."),
            "code",
            ev[:8],
        )

    ios_versions = {v for v, ts in versions.items() if any(t["kind"] == "app" for t in ts)}
    for g in android["gradle"]:
        if g["versionName"] and ios_versions and g["versionName"] not in ios_versions:
            f.add(
                "version", "MED",
                f'Android versionName {g["versionName"]} does not match iOS '
                f'{"/".join(sorted(ios_versions))}',
                "The same release carries two different version numbers across stores, "
                "which makes support reports and crash triage ambiguous.",
                "code",
                [{"type": "file", "path": g["path"], "line": g["line"],
                  "excerpt": f'versionName "{g["versionName"]}"'}],
            )

    builds = {t["buildNumber"] for t in targets if t["buildNumber"]}
    if len(builds) > 1:
        f.add(
            "version", "LOW",
            "CURRENT_PROJECT_VERSION differs across targets: " + ", ".join(sorted(builds)),
            "Build numbers that drift between an app and its extensions are usually "
            "accidental. Apple enforces the short version string, not this one, so it "
            "rarely blocks an upload.",
            "code",
            [e for t in targets if t["buildNumber"]
             and (e := cite(t, "CURRENT_PROJECT_VERSION",
                            f'{t["kind"]} {t["bundleId"]} ({t["configuration"]})'))][:8],
        )

    # ---- privacy manifest vs tracking SDKs ---------------------------------
    idfa = sig["trackingSdks"].get("idfa") or []
    att_declared = any("NSUserTrackingUsageDescription" in p["usageDescriptions"] for p in plists)

    if manifests:
        for pm in manifests:
            if pm["tracking"] is False and (idfa or att_declared):
                ev = [{"type": "file", "path": pm["path"], "line": pm["trackingLine"],
                       "excerpt": pm["trackingExcerpt"] or "<key>NSPrivacyTracking</key>"}]
                for p in plists:
                    meta = p["usageDescriptions"].get("NSUserTrackingUsageDescription")
                    if meta and meta["line"]:
                        ev.append({"type": "file", "path": p["path"], "line": meta["line"],
                                   "excerpt": meta["excerpt"],
                                   "note": "app prompts for tracking authorisation"})
                        break
                f.add(
                    "privacy", "HIGH",
                    f'{pm["path"]} declares NSPrivacyTracking false while the app ships '
                    f'tracking SDKs ({", ".join(idfa) or "ATT prompt present"})',
                    "The privacy manifest, the App Store privacy labels and the code must "
                    "agree. A manifest denying tracking while an ad SDK reads the advertising "
                    "identifier is the inconsistency Apple's automated scan looks for.",
                    "code", ev,
                )
            if pm["collectedDataTypeCount"] == 0 and (idfa or sig["trackingSdks"].get("analytics")):
                f.add(
                    "privacy", "MED",
                    f'{pm["path"]} declares no collected data types while analytics or ad '
                    f'SDKs are present',
                    "An empty NSPrivacyCollectedDataTypes array asserts the app collects "
                    "nothing. That contradicts any listing which declares collected data.",
                    "code",
                    [{"type": "file", "path": pm["path"],
                      "line": pm["collectedLine"] or pm["trackingLine"],
                      "excerpt": pm["collectedExcerpt"] or pm["trackingExcerpt"]}],
                )
    else:
        searched = [os.path.join(os.path.dirname(p["path"]), "PrivacyInfo.xcprivacy")
                    for p in plists] or ["ios/PrivacyInfo.xcprivacy"]
        f.add(
            "privacy", "HIGH",
            "No PrivacyInfo.xcprivacy found in the app target",
            "A privacy manifest declaring required-reason API usage has been mandatory for "
            "App Store submissions since 1 May 2024. Without one the upload is rejected.",
            "code",
            [{"type": "absence", "paths": sorted(set(searched))}],
        )

    # ---- permissions, both directions --------------------------------------
    for key in perms["unused"]:
        meta = perms["declared"][key]
        sev = "MED"
        extra = ""
        if "LocationAlways" in key or key == "NSLocationAlwaysUsageDescription":
            has_bg_location = any("location" in (m or "").lower()
                                  for p in plists for m in p["backgroundModes"])
            if not has_bg_location:
                extra = (" UIBackgroundModes does not include \"location\" either, so nothing "
                         "in the app can use background location.")
        f.add(
            "permissions", sev,
            f'{key} is declared but no code exercises it',
            f'Requesting a permission the app never uses is a data-minimisation problem, and '
            f'reviewers ask what it is for.{extra}',
            "code",
            [
                {"type": "file", "path": meta["plist"], "line": meta["line"],
                 "excerpt": meta["excerpt"]},
                {"type": "search", "patterns": meta["knownSymbols"],
                 "extensions": list(SOURCE_EXTS), "hits": 0},
            ],
        )

    for item in perms["undeclared"]:
        f.add(
            "permissions", "BLOCKER",
            f'Code uses a capability requiring {item["key"]}, which is not declared',
            "iOS terminates the app the first time a protected API is called without its "
            "usage-description key present. A reviewer hits this immediately.",
            "code",
            [{"type": "file", "path": h["path"], "line": h["line"], "excerpt": h["excerpt"]}
             for h in item["usedAt"]],
        )

    # ---- login wall --------------------------------------------------------
    if "otpSms" in sig["loginKinds"]:
        h = sig["loginKinds"]["otpSms"][0]
        f.add(
            "login", "BLOCKER",
            "Sign-in requires an SMS one-time code",
            "An App Review reviewer cannot receive an SMS. Unless the demo number in App "
            "Store Connect bypasses SMS on the backend, the reviewer cannot get past the "
            "login wall and the submission is rejected as incomplete.",
            "backend",
            [{"type": "file", "path": h["path"], "line": h["line"], "excerpt": h["excerpt"]}],
            note="Confirm the demo credentials work end to end. No tool can verify this.",
        )

    # ---- region lock -------------------------------------------------------
    region_evidence, region_reasons = [], []
    if sig["paymentUrlSchemes"]:
        for region, schemes in sig["paymentUrlSchemes"].items():
            region_reasons.append(f'{region.upper()} payment app hand-offs ({", ".join(schemes[:6])})')
    regional_pay = sig["paymentSdks"].get("regional") or []
    if regional_pay:
        region_reasons.append(f'region-specific payment SDKs ({", ".join(regional_pay)})')
    if len(sig["currencies"]) == 1:
        code, loc = next(iter(sig["currencies"].items()))
        region_reasons.append(f"a single currency in the codebase ({code})")
        region_evidence.append({"type": "file", "path": loc["path"], "line": loc["line"],
                                "excerpt": loc.get("excerpt")})
    if sig["postalValidators"]:
        pv = sig["postalValidators"][0]
        region_reasons.append(f'a country-specific postal field ({pv["needle"]})')
        region_evidence.append({"type": "file", "path": pv["path"], "line": pv["line"],
                                "excerpt": pv["excerpt"]})

    if len(region_reasons) >= 2:
        f.add(
            "region", "HIGH",
            "The code only supports one market: " + "; ".join(region_reasons),
            "An app shipped to territories where checkout, delivery or address entry cannot "
            "work is incomplete in those territories. Compare this against the territory "
            "count on the Pricing and Availability page.",
            "store", region_evidence[:6] or [{"type": "search", "patterns": ["currency"],
                                              "extensions": list(SOURCE_EXTS), "hits": 0}],
            note="Narrowing territories may also retire any EU-specific obligation.",
        )

    # ---- things this script cannot settle ----------------------------------
    f.skip("SDK and Xcode floor", "Requires the current minimum from Apple's Upcoming "
           f'Requirements page. Detected locally: {toolchain.get("xcode") or "unknown"}.')
    f.skip("Territory list", "The listing shows a count, not the countries. Screenshot gives "
           "the count only.")
    f.skip("Privacy label accuracy", "App Store privacy labels have no API and are not in the "
           "repository. Collected by screenshot.")
    f.skip("DSA trader status", "Account-level, no API, not in the repository. Collected by "
           "screenshot.")
    f.skip("Mac and Vision Pro availability", "No API and not in the repository. Collected by "
           "screenshot.")
    f.skip("Description and promotional claims", "Requires the listing text plus judgement "
           "about what the app actually does.")
    if not project["verified"]:
        f.skip("Framework-specific checks",
               f'Framework {project["framework"] or "unknown"} is detected but unverified in '
               f'this version. Findings from the shared checks still apply.')


def detect_toolchain(targets):
    xcode = None
    try:
        out = subprocess.run(["xcodebuild", "-version"], capture_output=True,
                             text=True, timeout=20)
        if out.returncode == 0:
            xcode = out.stdout.strip().splitlines()[0]
    except (OSError, subprocess.SubprocessError):
        pass
    return {
        "xcode": xcode,
        "deploymentTargets": sorted({t["deploymentTarget"] for t in targets
                                     if t["deploymentTarget"]}),
        "deviceFamilies": sorted({t["deviceFamily"] for t in targets if t["deviceFamily"]}),
    }


# ── main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Deterministic project read for "
                                             "check-appstore-details.")
    ap.add_argument("--path", default=os.getcwd(), help="project root (default: cwd)")
    ap.add_argument("--out", default=None,
                    help="output file (default: <path>/.check-appstore-details/findings.json)")
    ap.add_argument("--print", dest="do_print", action="store_true",
                    help="also print the JSON to stdout")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        print(f"scan-project: not a directory: {root}", file=sys.stderr)
        return 2

    out_path = args.out or os.path.join(root, ".check-appstore-details", "findings.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Keep the working directory out of git without editing the target repo:
    # .git/info/exclude is untracked.
    exclude = os.path.join(root, ".git", "info", "exclude")
    if os.path.isdir(os.path.dirname(exclude)):
        current = read_text(exclude)
        if ".check-appstore-details/" not in current:
            try:
                with open(exclude, "a") as fh:
                    fh.write("\n.check-appstore-details/\n")
            except OSError:
                pass

    signals = load_signals()
    if not signals:
        print(f"scan-project: cannot read {SIGNALS_PATH}", file=sys.stderr)
        return 2

    provenance = scan_provenance(root)
    project = detect_framework(root)

    xcodeprojs = sorted(walk_dirs(root, lambda n: n.endswith(".xcodeproj")))
    targets = []
    for proj in xcodeprojs:
        pbx = os.path.join(proj, "project.pbxproj")
        if os.path.exists(pbx):
            targets.extend(parse_pbxproj(pbx, root))
    targets = classify_targets(targets)

    plists = scan_info_plists(root)
    manifests = scan_privacy_manifests(root)
    android = scan_android(root)
    index = build_source_index(root)
    sig = detect_signals(root, project["dependencies"], index, plists, signals)
    perms = audit_permissions(index, plists, signals)
    toolchain = detect_toolchain(targets)

    f = Findings()
    if not xcodeprojs:
        f.skip("All iOS checks", "No .xcodeproj found under this path, so there is no iOS app "
                                 "to compare a listing against.")
    else:
        evaluate(root, project, targets, plists, manifests, android, sig, perms, toolchain, f)

    project.pop("dependencies", None)
    for p in plists:
        p.pop("absPath", None)

    payload = {
        "scan": provenance,
        "scanner": {"name": "check-appstore-details/scan-project.py", "version": "0.1.0"},
        "project": project,
        "iosProjects": [os.path.relpath(p, root) for p in xcodeprojs],
        "targets": targets,
        "infoPlists": plists,
        "privacyManifests": manifests,
        "android": android,
        "signals": sig,
        "permissions": perms,
        "toolchain": toolchain,
        "sourceFilesScanned": len(index),
        "findings": f.items,
        "notChecked": f.not_checked,
    }

    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")

    if args.do_print:
        print(json.dumps(payload, indent=2))
    else:
        loc = provenance
        where = f'{loc["branch"] or "no branch"} @ {loc["commit"] or "no commit"}'
        dirty = "dirty" if loc["dirty"] else "clean"
        print(f'read {where}, working tree {dirty}')
        print(f'framework: {project["framework"] or "unknown"}'
              f'{"" if project["verified"] else " (unverified in this version)"}')
        print(f'targets: {len(targets)} · source files: {len(index)} · '
              f'findings: {len(f.items)} · not checked: {len(f.not_checked)}')
        print(f'wrote {os.path.relpath(out_path, root)}')

    return 0


if __name__ == "__main__":
    sys.exit(main())
