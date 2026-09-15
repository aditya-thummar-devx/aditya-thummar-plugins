# init-mcp-disable

A Claude Code plugin that lists the **claude.ai MCP connectors** loaded in your current project
and turns off the ones you don't want — **for that project only**. It works one connector at a
time and can remember a keep-list, so the next project is confirm-and-go.

> Not affiliated with, endorsed by, or connected to Slack, Google, Notion, or any other company.
> Connector names are shown only because they are what your workspace has enabled.

## Why

The `claude.ai *` connectors are enabled by a workspace admin, so **every new project starts with
~30 of them loaded** — most not even authenticated, but all still shipping tool definitions into
your context before you type a word.

The only per-project off switch is the `/mcp disable <name>` slash command, and a skill cannot type
slash commands. So this plugin writes the same config key directly:

```
~/.claude.json  →  projects["<project dir>"].disabledMcpServers
```

## What it does

- **Lists** every claude.ai connector for the current project, with auth state, enabled/disabled,
  and a keep marker. Backs up `~/.claude.json` first, every run.
- **Asks** which to disable — by number, `all`, ranges like `3-8`, or `all except 5,11`.
- **Disables** one connector per call, so every write is visible and a failure doesn't take the
  rest down with it.
- **Remembers a keep-list** (optional) in the plugin's persistent data directory, shared across
  projects and safe across plugin updates.

## Install

```
/plugin install init-mcp-disable@aditya-thummar-plugins
```

Then run `/init-mcp-disable` in any project.

## Limits

- **Per project.** Other projects are untouched.
- **Manual invoke only.** It never runs on its own.
- **claude.ai connectors only.** Local and user-scope servers, `plugin:*`, `claude-in-chrome` and
  `ide` are refused by the helper — it rejects any name not starting with `claude.ai `.
- **Takes effect on the next launch.** Restart Claude Code after running it.
- **Undo is `/mcp enable <name>`**, typed by you. This plugin does not re-enable.
- It never touches `disableClaudeAiConnectors` in `~/.claude/settings.json` — that is a global
  all-or-nothing switch and is deliberately out of scope.

## Files it touches

| Path | What |
|---|---|
| `~/.claude.json` | The only file written — one project's `disabledMcpServers` list |
| `~/.claude/backups/claude.json.<epoch>.bak` | Backup, written before every list |
| `${CLAUDE_PLUGIN_DATA}/init-mcp-disable-keep.json` | Your saved keep-list, if you save one |

## License

MIT
