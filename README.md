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

## Layout

```
.claude-plugin/marketplace.json    # this marketplace
plugins/
├── non-tech-content/              # plugin: skill "generate"
└── check-appstore-details/        # plugin: skill + references + scripts
```
