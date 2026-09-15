# aditya-thummar-plugins

Aditya Thummar's Claude Code plugin marketplace. Add it once, then install any plugin below.

## Add the marketplace

```
/plugin marketplace add aditya-thummar-devx/aditya-thummar-plugins
```

## Plugins

### non-tech-content

House writing style for plain-language documentation that a non-technical reader — an executive, a
CEO, a new joiner — can fully understand. Generates or rewrites any doc into a clear, jargon-free
form. Project- and stack-agnostic.

```
/plugin install non-tech-content@aditya-thummar-plugins
```

Invoke with `/non-tech-content:generate`, or just ask it to "rewrite this so a CEO can read it."

### check-appstore-details

Audit an iOS app's App Store listing against its own codebase before submission, then walk through
fixing each problem one page at a time. Fetches current Apple policy at run time, needs no App Store
Connect credentials, and verifies every fix before moving on.

```
/plugin install check-appstore-details@aditya-thummar-plugins
```

### init-mcp-disable

List the `claude.ai *` MCP connectors loaded in the current project and turn off the ones you don't
want — for that project only. Every new project starts with ~30 admin-enabled connectors shipping
tool definitions into your context; this trims them, one connector at a time, backing up your config
first and optionally remembering a keep-list for next time.

```
/plugin install init-mcp-disable@aditya-thummar-plugins
```

Invoke with `/init-mcp-disable`. Restart Claude Code afterwards for it to take effect.

## Layout

```
.claude-plugin/marketplace.json    # this marketplace
plugins/
├── non-tech-content/              # plugin: skill "generate"
├── check-appstore-details/        # plugin: skill + references + scripts
├── prepare-handover-docs/         # plugin: 2 skills (React Native, Expo) + references + scripts
├── update-docs/                   # plugin: skill + references + scripts
└── init-mcp-disable/              # plugin: skill + script
```
