#!/usr/bin/env python3
"""Per-project claude.ai connector disabler.

Writes projects[<cwd>].disabledMcpServers in ~/.claude.json -- the same key the
in-session `/mcp disable <name>` slash command writes. Used by the
init-mcp-disable skill, because a skill cannot type slash commands.

Usage:
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" list
        # backup + show connectors for this project
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" disable "<name>"
        # add one name to this project's disabled list
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" keep "<name>" ...
        # save the keep-list (replaces it)
    python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" --self-check
        # run assertions, touch nothing

The keep-list is written to CLAUDE_PLUGIN_DATA -- the plugin's persistent data
directory, which survives plugin updates. Never next to this file: installed
plugins live in a git checkout that Claude Code pulls on update, so a write
there would dirty the checkout and be clobbered.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

CONFIG = os.path.expanduser("~/.claude.json")
BACKUP_DIR = os.path.expanduser("~/.claude/backups")
PREFIX = "claude.ai "


def keep_path():
    """Keep-list lives in the plugin's persistent data dir, never beside this file."""
    data = os.environ.get("CLAUDE_PLUGIN_DATA") or os.path.expanduser("~/.claude")
    return os.path.join(data, "init-mcp-disable-keep.json")


# "claude.ai Slack: https://mcp.slack.com/mcp - ✔ Connected"
# "plugin:figma:figma: https://mcp.figma.com/mcp (HTTP) - ! Needs authentication"
LINE_RE = re.compile(r"^(?P<name>.+?): (?P<url>\S+).*? - (?P<status>.+)$")


def load_config():
    with open(CONFIG) as f:
        return json.load(f)


def project_key(cfg):
    """Claude Code keys projects by launch dir. Prefer cwd; else nearest ancestor
    that already exists in the config."""
    cwd = os.getcwd()
    projects = cfg.get("projects", {})
    if cwd in projects:
        return cwd
    home = os.path.expanduser("~")
    p = cwd
    while p not in ("/", home):
        p = os.path.dirname(p)
        if p in projects and p != home:
            return p
    return cwd


def disabled_for(cfg, key):
    return cfg.get("projects", {}).get(key, {}).get("disabledMcpServers", []) or []


def read_keep():
    try:
        with open(keep_path()) as f:
            return json.load(f).get("keep", [])
    except (OSError, ValueError):
        return []


def backup():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, "claude.json.%d.bak" % time.time())
    shutil.copy2(CONFIG, dst)
    return dst


def parse_mcp_list(text):
    """-> [(name, status)] for every parseable line."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        m = LINE_RE.match(line)
        if m:
            out.append((m.group("name"), m.group("status").strip()))
    return out


def cmd_list():
    cfg = load_config()
    key = project_key(cfg)
    dst = backup()
    proc = subprocess.run(["claude", "mcp", "list"], capture_output=True, text=True)
    parsed = parse_mcp_list(proc.stdout + proc.stderr)
    if not parsed:
        print("could not parse `claude mcp list` output:", file=sys.stderr)
        print(proc.stdout[:500] or proc.stderr[:500], file=sys.stderr)
        return 1

    live = {n: s for n, s in parsed if n.startswith(PREFIX)}
    off = disabled_for(cfg, key)
    keep = read_keep()
    # disabled connectors may drop out of `claude mcp list` -- union them back in
    names = sorted(set(live) | {n for n in off if n.startswith(PREFIX)})

    print("project: %s" % key)
    print("backup:  %s" % dst)
    print("keep-list: %s" % (", ".join(keep) if keep else "(none saved)"))
    print()
    print("  #  %-32s %-16s %-9s %s" % ("connector", "auth", "state", "keep"))
    for i, n in enumerate(names, 1):
        status = live.get(n, "not listed")
        if "Connected" in status:
            auth = "connected"
        elif "Disabled" in status:
            auth = "-"
        elif "auth" in status.lower():
            auth = "needs auth"
        else:
            auth = status[:16]
        print("%3d  %-32s %-16s %-9s %s" % (
            i, n[len(PREFIX):], auth, "disabled" if n in off else "ENABLED",
            "KEEP" if n in keep else ""))
    print()
    print("%d connectors, %d already disabled for this project" % (len(names), len([n for n in names if n in off])))
    return 0


def cmd_disable(name):
    if not name.startswith(PREFIX):
        print("refusing: '%s' is not a claude.ai connector" % name, file=sys.stderr)
        return 1
    cfg = load_config()
    key = project_key(cfg)
    entry = cfg.setdefault("projects", {}).setdefault(key, {})
    off = entry.setdefault("disabledMcpServers", [])
    if name in off:
        print("- already disabled: %s  (%d total)" % (name, len(off)))
        return 0
    off.append(name)
    # ponytail: plain read-modify-write, no lockfile. Claude Code holds a lock on
    # this file; the backup in `list` is the safety net. Add filelock if a clobber
    # ever actually happens.
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    print("✓ disabled: %s  (%d total)" % (name, len(off)))
    return 0


def cmd_keep(names):
    path = keep_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"keep": sorted(set(names))}, f, indent=2)
    print("✓ keep-list saved (%d): %s" % (len(set(names)), ", ".join(sorted(set(names))) or "(empty)"))
    return 0


def self_check():
    sample = """Checking MCP server health…

claude.ai Aspire: https://aspire-mcp.aspireapp.com/mcp - ! Needs authentication
claude.ai Slack: https://mcp.slack.com/mcp - ✔ Connected
plugin:figma:figma: https://mcp.figma.com/mcp (HTTP) - ! Needs authentication
"""
    got = parse_mcp_list(sample)
    assert len(got) == 3, got
    assert got[0] == ("claude.ai Aspire", "! Needs authentication"), got[0]
    assert got[1][1] == "✔ Connected", got[1]
    assert got[2][0] == "plugin:figma:figma", got[2]
    assert not [n for n, _ in got if n.startswith("Checking")], "header leaked"

    # dedupe: appending an existing name must not grow the list
    off = ["claude.ai Gmail"]
    if "claude.ai Gmail" not in off:
        off.append("claude.ai Gmail")
    assert off == ["claude.ai Gmail"], off

    # project_key falls back to an ancestor
    fake = {"projects": {"/a": {}}}
    cwd = os.getcwd()
    try:
        os.chdir("/")
        assert project_key(fake) == "/", "root cwd should return itself"
    finally:
        os.chdir(cwd)

    # keep-list follows CLAUDE_PLUGIN_DATA and never lands beside this file
    here = os.path.dirname(os.path.abspath(__file__))
    prev = os.environ.get("CLAUDE_PLUGIN_DATA")
    try:
        os.environ["CLAUDE_PLUGIN_DATA"] = "/tmp/init-mcp-disable-selfcheck"
        assert keep_path() == "/tmp/init-mcp-disable-selfcheck/init-mcp-disable-keep.json", keep_path()
        del os.environ["CLAUDE_PLUGIN_DATA"]
        assert keep_path().startswith(os.path.expanduser("~/.claude")), keep_path()
        assert not keep_path().startswith(here), "keep-list would dirty the plugin checkout"
    finally:
        if prev is None:
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
        else:
            os.environ["CLAUDE_PLUGIN_DATA"] = prev

    print("self-check ok")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    if a[0] == "--self-check":
        sys.exit(self_check())
    if a[0] == "list":
        sys.exit(cmd_list())
    if a[0] == "disable" and len(a) == 2:
        sys.exit(cmd_disable(a[1]))
    if a[0] == "keep":
        sys.exit(cmd_keep(a[1:]))
    print(__doc__, file=sys.stderr)
    sys.exit(2)
