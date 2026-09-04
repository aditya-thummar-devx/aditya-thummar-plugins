# prepare-handover-docs

A Claude Code plugin that builds a **client-handover Google Doc** for a mobile app —
one native tab per area — by reading the current project and asking you only for the
things that live outside it (store status, account owners, Drive links). It works one
step at a time and **writes nothing until you confirm**.

> Not affiliated with, endorsed by, or connected to Google, Apple, or any other
> company. "Google Docs", "App Store", "Play Store", and "Firebase" are named only to
> describe what the tool documents.

## Why

When a mobile app is handed to a client, the code is only half the story. The other
half — production env config, Firebase project, signing keys and certificates, store
accounts and submission status, and how to build/release/roll back — lives in people's
heads and scattered consoles. This packages that into one structured document, filled
from the repo where possible so it stays accurate, with no secret values in it.

## What it does

- **Detects the project** at invoke time (app name, bundle id / package, versions,
  Firebase, env files) and uses *that* project's identity everywhere — no hardcoded
  names. Two skills: **React Native** (default) and **Expo/EAS** (`-expo`).
- **Builds native Google Docs tabs** via a bundled engine and an OAuth token you
  supply (guided step by step). Default tabs: Overview, Env, Firebase, App Store,
  Play Store, Release & Rollback — you can add or remove any.
- **One step at a time.** Each tab: announces what it will add, auto-fills from the
  repo, asks you for the rest, shows a sign-off view, writes only on your confirmation,
  then verifies the write and stops for you to check before the next tab.
- **Keeps secrets out.** Reads key *names* from `.env.example` (never `.env`), records
  keystore fingerprints not passwords, and points every secret at a locked Drive folder
  or vault — never into the document.

## What it deliberately does not do

- **No secret values in the doc.** Ever. Tokens, passwords, and keys stay in the Drive
  folder / a password manager.
- **No store credentials.** It uses no App Store Connect or Play API. Store status,
  build numbers, and account owners are provided by you.
- **No in-place tab editing.** The Docs API cannot delete a tab and the engine only
  appends, so editing a tab means you delete it and the skill regenerates it.
- **React Native and Expo only.** Other stacks are not detected; the skill says so
  rather than guessing.

## Install

Local development:

```
claude --plugin-dir /path/to/prepare-handover-docs
```

Or via a marketplace, once published:

```
/plugin marketplace add <owner>/aditya-thummar-plugins
/plugin install prepare-handover-docs
```

## Use

From inside a mobile project:

```
/prepare-handover-docs         # React Native (bare)
/prepare-handover-docs-expo    # Expo / EAS
```

It detects the app, shows the tabs it will create, asks whether to add/remove any,
collects the target doc + token, then walks the tabs with you.

## Getting the OAuth token

The engine writes to your Google Doc with an OAuth access token you provide (scopes
`documents` + `drive`). The skill guides you through minting one from the
[OAuth 2.0 Playground](https://developers.google.com/oauthplayground); see
`references/token-guide.md`. Tokens last about an hour — the skill asks for a fresh one
whenever a write fails with 401.

## How it's built

```
prepare-handover-docs/
├── scripts/
│   └── build_doc.py            # engine: content spec -> native Google Docs tab (stdlib only)
├── references/
│   ├── interaction-protocol.md # the per-step confirm/write/verify loop
│   ├── token-guide.md          # OAuth Playground, step by step
│   ├── drive-layout.md         # recommended handover Drive folder structure
│   ├── spec-format.md          # engine block types + hard constraints
│   ├── tab-templates.md        # generic templates: Overview, Env, Firebase, App/Play Store
│   ├── release-tab-bare.md     # Release & Rollback — bare React Native
│   ├── release-tab-expo.md     # Release & Rollback — Expo/EAS
│   ├── detection-bare.md       # where to read facts — bare React Native
│   └── detection-expo.md       # where to read facts — Expo
└── skills/
    ├── prepare-handover-docs/SKILL.md        # bare RN run flow
    └── prepare-handover-docs-expo/SKILL.md   # Expo run flow
```

The engine only builds tabs from a spec and verifies the write; all judgement — what to
gather, what to ask, what goes in each tab — lives in the skill and its references.

## Licence

MIT. See [LICENSE](LICENSE).
