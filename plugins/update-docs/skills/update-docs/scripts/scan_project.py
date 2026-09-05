#!/usr/bin/env python3
"""
Deterministic structure read for update-docs.

Reads any project and emits one structure.json describing its stack, entry
points, top-level source layout, candidate documentable units (screens / routes
/ endpoints / public API, per kind), and the docs it already has. It never
edits the project it is pointed at.

Everything here must be reproducible: the same tree in the same state produces
the same output. Judgement — which flows matter, what the tree should be, what
is undocumented — belongs to the skill, not to this file. This script only
gathers signals the skill reasons over.

Two rules this script exists to enforce mechanically:

  1. Stack kind is inferred from MANIFESTS and dependencies, never from a single
     file's presence. `app.json` ships in bare React Native too; `index.html`
     appears in libraries. One weak signal never decides the kind.

  2. The existing-docs inventory is exhaustive and honest. A restructure that
     misses one doc orphans it; the skill must see every markdown file that
     already exists, with its path, so nothing is silently left behind.

Usage:
  python3 scan_project.py [--path DIR] [--out FILE] [--print]
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

WORK_DIR = ".update-docs"

SKIP_PARTS = tuple(os.sep + p + os.sep for p in (
    ".git", "node_modules", "Pods", "build", "dist", "out", ".next", ".expo",
    "DerivedData", "vendor", ".gradle", ".idea", "coverage", "__pycache__",
    ".venv", "venv", "target", ".dart_tool", "Carthage", WORK_DIR,
))

SOURCE_EXTS = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte",
               ".py", ".go", ".rs", ".java", ".kt", ".swift", ".rb", ".php",
               ".dart", ".cs", ".scala", ".ex", ".exs")
MAX_SOURCE_BYTES = 2_000_000

# Top-level dirs that usually hold source, in rough priority order.
SOURCE_DIR_NAMES = ("src", "app", "lib", "packages", "apps", "pkg", "internal",
                    "cmd", "components", "server", "backend", "frontend", "core")


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


def walk_files(root, match):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not skipped(os.path.join(dirpath, d))]
        for name in filenames:
            full = os.path.join(dirpath, name)
            if match(name) and not skipped(full):
                yield full


def git(root, *args):
    try:
        out = subprocess.run(["git", "-C", root, *args],
                             capture_output=True, text=True, timeout=15)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def rel(root, path):
    return os.path.relpath(path, root)


# ── provenance ──────────────────────────────────────────────────────────────

def scan_provenance(root):
    """What was actually read. Docs derived from a stale tree are wrong docs."""
    is_repo = bool(git(root, "rev-parse", "--is-inside-work-tree"))
    status = git(root, "status", "--porcelain") if is_repo else ""
    return {
        "path": root,
        "isGitRepo": is_repo,
        "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD") or None,
        "commit": git(root, "rev-parse", "--short", "HEAD") or None,
        "dirty": bool(status),
        "dirtyFileCount": len([l for l in status.splitlines() if l.strip()]),
        "scannedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ── stack detection (manifest + dependency driven) ───────────────────────────

def load_json(path):
    try:
        return json.loads(read_text(path) or "{}")
    except json.JSONDecodeError:
        return {}


def detect_stack(root):
    """
    Kind is inferred from manifests, not from any one file's presence. The
    failure this avoids: calling every repo with an index.html a 'web app'.
    Returns a language, a framework, and a coarse KIND the skill adapts its
    vocabulary to (mobile / web / backend / library / cli / monorepo / unknown).
    """
    manifests, languages, frameworks = [], set(), set()

    pkg = load_json(os.path.join(root, "package.json"))
    deps = {}
    if pkg:
        manifests.append("package.json")
        languages.add("javascript/typescript")
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for name, fw in (("expo", "expo"), ("react-native", "react-native"),
                         ("next", "next.js"), ("nuxt", "nuxt"), ("@remix-run/react", "remix"),
                         ("@angular/core", "angular"), ("vue", "vue"), ("svelte", "svelte"),
                         ("react", "react"), ("@nestjs/core", "nestjs"),
                         ("express", "express"), ("fastify", "fastify"), ("koa", "koa")):
            if name in deps:
                frameworks.add(fw)
        if pkg.get("workspaces") or os.path.isdir(os.path.join(root, "packages")):
            frameworks.add("monorepo")

    for fname, lang in (("pyproject.toml", "python"), ("setup.py", "python"),
                        ("requirements.txt", "python"), ("go.mod", "go"),
                        ("Cargo.toml", "rust"), ("pom.xml", "java"),
                        ("build.gradle", "java/kotlin"), ("Gemfile", "ruby"),
                        ("composer.json", "php"), ("pubspec.yaml", "dart/flutter")):
        if os.path.exists(os.path.join(root, fname)):
            manifests.append(fname)
            languages.add(lang)

    py = read_text(os.path.join(root, "pyproject.toml")) + read_text(os.path.join(root, "requirements.txt"))
    for needle, fw in (("django", "django"), ("flask", "flask"), ("fastapi", "fastapi")):
        if re.search(needle, py, re.I):
            frameworks.add(fw)
    if re.search(r"^\s*flutter\s*:", read_text(os.path.join(root, "pubspec.yaml")), re.M):
        frameworks.add("flutter")

    kind = classify_kind(root, deps, frameworks, pkg)
    return {
        "kind": kind,
        "languages": sorted(languages) or ["unknown"],
        "frameworks": sorted(frameworks),
        "manifests": manifests,
        "hasPackageJson": bool(pkg),
    }


def classify_kind(root, deps, frameworks, pkg):
    mobile = {"react-native", "expo", "flutter"}
    web = {"next.js", "nuxt", "remix", "angular", "vue", "svelte", "react"}
    backend = {"nestjs", "express", "fastify", "koa", "django", "flask", "fastapi"}
    if frameworks & mobile:
        return "mobile-app"
    if "monorepo" in frameworks:
        return "monorepo"
    if frameworks & backend:
        return "backend-api"
    if frameworks & web:
        return "web-app"
    # A package with a declared entry/exports and no app framework reads as a library.
    if pkg and (pkg.get("main") or pkg.get("exports") or pkg.get("module")) and not (frameworks & (web | backend | mobile)):
        return "library"
    if os.path.exists(os.path.join(root, "go.mod")) and os.path.isdir(os.path.join(root, "cmd")):
        return "cli"
    return "unknown"


# ── layout + candidate units ─────────────────────────────────────────────────

def top_level_source_dirs(root):
    dirs = []
    for name in sorted(os.listdir(root)):
        full = os.path.join(root, name)
        if os.path.isdir(full) and not name.startswith(".") and name in SOURCE_DIR_NAMES:
            dirs.append(name)
    return dirs


def subdirs(path):
    try:
        return sorted(d for d in os.listdir(path)
                      if os.path.isdir(os.path.join(path, d)) and not d.startswith("."))
    except OSError:
        return []


def candidate_units(root, kind):
    """
    Coarse, kind-adapted candidates for the skill to confirm — never the final
    word. mobile -> screens; web -> routes/pages; backend -> endpoints/handlers;
    everything -> the top-level source folders (modules). Deliberately shallow:
    the skill reads code for the real flows; this just points it at the right
    piles.
    """
    units = {"modules": [], "screens": [], "routes": [], "endpoints": []}

    # modules = top-level dirs under each source root (one level down)
    for sd in top_level_source_dirs(root):
        for child in subdirs(os.path.join(root, sd)):
            units["modules"].append(f"{sd}/{child}")

    def dirs_matching(*names):
        # docs/ holds documentation about the code, not code — never a candidate
        # unit, or the mirror pages under docs/ get mistaken for real screens.
        found = []
        for dp, dn, _ in os.walk(root):
            dn[:] = [d for d in dn if not skipped(os.path.join(dp, d)) and d != "docs"]
            for d in list(dn):
                if d.lower() in names:
                    found.append(rel(root, os.path.join(dp, d)))
        return sorted(set(found))

    def not_docs(paths):
        return [p for p in paths if p.split(os.sep)[0] != "docs"]

    if kind == "mobile-app":
        # folders literally named screens/, plus files/dirs ending in Screen
        for base in dirs_matching("screens", "pages", "views"):
            units["screens"] += [f"{base}/{c}" for c in subdirs(os.path.join(root, base))] or [base]
        screen_files = [rel(root, p) for p in walk_files(
            root, lambda n: re.search(r"(Screen|Page)\.(tsx|jsx|ts|js|dart|swift|kt)$", n))]
        units["screens"] = sorted(set(units["screens"] + screen_files))[:400]
    if kind in ("web-app", "monorepo"):
        for base in dirs_matching("pages", "routes", "app", "views"):
            units["routes"].append(base)
    if kind in ("backend-api", "monorepo"):
        units["endpoints"] = dirs_matching("routes", "controllers", "handlers", "endpoints", "api", "resolvers")

    for k in units:
        units[k] = not_docs(units[k])[:400]
    return units


def entry_points(root):
    found = []
    for name in ("index.js", "index.ts", "index.tsx", "App.tsx", "App.js", "main.py",
                 "main.go", "main.rs", "manage.py", "server.js", "app.py", "src/main.ts",
                 "src/index.ts", "cmd"):
        if os.path.exists(os.path.join(root, name)):
            found.append(name)
    return found


# ── existing docs inventory ──────────────────────────────────────────────────

def parse_front_matter(text):
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    fm = {}
    for line in text[4:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm


def inventory_docs(root):
    """Every markdown file, so a restructure orphans nothing. Flags whether each
    already carries front-matter (the staleness stamp the skill maintains)."""
    docs = []
    for path in walk_files(root, lambda n: n.lower().endswith((".md", ".mdx"))):
        r = rel(root, path)
        fm = parse_front_matter(read_text(path))
        docs.append({
            "path": r,
            "inDocsDir": r.startswith("docs" + os.sep) or r.startswith("docs/"),
            "isReadme": os.path.basename(path).lower().startswith("readme"),
            "hasFrontMatter": fm is not None,
            "frontMatterKeys": sorted(fm.keys()) if fm else [],
        })
    docs.sort(key=lambda d: d["path"])
    return docs


def convention_files(root):
    """Canonical rule files the docs should LINK to, never restate."""
    found = []
    for name in ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md", ".cursorrules",
                 "CONVENTIONS.md", "README.md"):
        if os.path.exists(os.path.join(root, name)):
            found.append(name)
    return found


# ── main ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Deterministic structure read for update-docs.")
    ap.add_argument("--path", default=os.getcwd(), help="project root (default: cwd)")
    ap.add_argument("--out", default=None,
                    help=f"output file (default: <path>/{WORK_DIR}/structure.json)")
    ap.add_argument("--print", dest="do_print", action="store_true",
                    help="also print the JSON to stdout")
    args = ap.parse_args()

    root = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.isdir(root):
        print(f"scan_project: not a directory: {root}", file=sys.stderr)
        return 2

    out_path = args.out or os.path.join(root, WORK_DIR, "structure.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    # Keep the working dir out of git without editing tracked files:
    # .git/info/exclude is itself untracked.
    exclude = os.path.join(root, ".git", "info", "exclude")
    if os.path.isdir(os.path.dirname(exclude)) and f"{WORK_DIR}/" not in read_text(exclude):
        try:
            with open(exclude, "a") as fh:
                fh.write(f"\n{WORK_DIR}/\n")
        except OSError:
            pass

    provenance = scan_provenance(root)
    stack = detect_stack(root)
    source_count = sum(1 for _ in walk_files(root, lambda n: n.endswith(SOURCE_EXTS)))
    existing = inventory_docs(root)

    payload = {
        "scan": provenance,
        "scanner": {"name": "update-docs/scan_project.py", "version": "0.1.0"},
        "stack": stack,
        "entryPoints": entry_points(root),
        "topLevelSourceDirs": top_level_source_dirs(root),
        "candidateUnits": candidate_units(root, stack["kind"]),
        "conventionFiles": convention_files(root),
        "sourceFileCount": source_count,
        "existingDocs": existing,
        "existingDocsCount": len(existing),
        "docsWithFrontMatter": sum(1 for d in existing if d["hasFrontMatter"]),
    }

    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")

    if args.do_print:
        print(json.dumps(payload, indent=2))
    else:
        p = provenance
        print(f'read {p["branch"] or "no branch"} @ {p["commit"] or "no commit"}, '
              f'working tree {"dirty" if p["dirty"] else "clean"}')
        print(f'kind: {stack["kind"]} · languages: {", ".join(stack["languages"])} · '
              f'frameworks: {", ".join(stack["frameworks"]) or "none"}')
        u = payload["candidateUnits"]
        print(f'source files: {source_count} · modules: {len(u["modules"])} · '
              f'screens: {len(u["screens"])} · routes: {len(u["routes"])} · '
              f'endpoints: {len(u["endpoints"])}')
        print(f'existing docs: {len(existing)} '
              f'({payload["docsWithFrontMatter"]} with front-matter)')
        print(f'wrote {rel(root, out_path)}')

    return 0


if __name__ == "__main__":
    sys.exit(main())
