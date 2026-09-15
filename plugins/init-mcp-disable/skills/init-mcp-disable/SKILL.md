---
name: init-mcp-disable
description: "List this project's claude.ai MCP connectors and disable the ones the user doesn't want, per project. Use when the user runs /init-mcp-disable, or asks to turn off / disable / clean up MCP servers or connectors in a project, complains that every new project loads all the admin-enabled claude.ai connectors, or wants to cut the MCP tool bloat in their context."
version: 1.0.0
trigger: /init-mcp-disable
allowed-tools: [Bash, AskUserQuestion]
---

# /init-mcp-disable

Turn off unwanted `claude.ai *` MCP connectors **for the current project only**.

## Why this exists

The claude.ai connectors are enabled by the workspace admin, so every new project starts with ~30 of them loaded — most not even authenticated, but still shipping tool definitions into context. The only per-project off switch is the `/mcp disable <name>` slash command, and a skill cannot type slash commands. So this skill writes the same config key directly:

`~/.claude.json` → `projects["<project dir>"].disabledMcpServers`

## Scope and limits

- **Per project.** Only the current project directory is touched. Other projects are untouched.
- **Manual invoke only.** Never run this unprompted.
- **claude.ai connectors only.** Local/user-scope servers, `plugin:*`, `claude-in-chrome`, `ide` are never touched — the helper refuses any name not starting with `claude.ai `.
- **Takes effect on next launch.** The write does not unload tools mid-session. Always end by telling the user to restart Claude Code.
- **Undo is `/mcp enable <name>`**, typed by the user. This skill does not re-enable.
- Never touch `disableClaudeAiConnectors` in `~/.claude/settings.json` — that is a global all-or-nothing switch and is out of scope.

## Steps

**1. List.**

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" list
```

Takes 5–20s (it health-checks every endpoint) and backs up `~/.claude.json` first. Show the user the table as-is: number, connector, auth state, enabled/disabled, keep marker.

**2. Ask what to disable.**

- **If the keep-list is non-empty:** propose disabling everything currently `ENABLED` except the `KEEP` rows. Name the ones that would go and the ones that would stay, and ask to confirm or edit.
- **If no keep-list:** ask which numbers to disable. Accept `all`, `1,4,9`, ranges like `3-8`, and `all except 5,11`.

Resolve the answer to full names (`claude.ai ` + the name in the table). Skip anything already `disabled`.

**3. Disable, one call per connector.**

One bash call each, so every write is visible:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" disable "claude.ai Indeed"
```

Echo each returned line (`✓ disabled: … (n total)`) as it comes back. If one fails, report it and keep going with the rest.

**4. Offer to save the keep-list.**

Ask whether to remember the connectors that were left enabled, so the next project is confirm-and-go:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py" keep "claude.ai Slack" "claude.ai Google Drive"
```

This replaces the whole list. Saved to the plugin's persistent data directory, so it survives plugin updates and is shared across projects.

**5. Summarise.**

Report: how many disabled, how many kept, the project path, and the backup path from step 1. Then tell the user plainly: **restart Claude Code for this to take effect.**

## Files

| Path | What |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/scripts/mcp_toggle.py` | Helper. `list`, `disable <name>`, `keep <names...>`, `--self-check` |
| `${CLAUDE_PLUGIN_DATA}/init-mcp-disable-keep.json` | Saved keep-list. Created on first save. Falls back to `~/.claude/` outside a plugin install |
| `~/.claude/backups/claude.json.<epoch>.bak` | Backup, written by every `list` run |
