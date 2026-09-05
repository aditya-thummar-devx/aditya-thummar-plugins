---
name: prepare-handover-docs
description: Build a client-handover Google Doc for a bare React Native mobile app — one native tab per area (env config, Firebase, App Store, Play Store, release & rollback, and an overview). Detects the current project and fills every tab from the repo plus the few things only the user knows (store status, account owners, Drive links), one step at a time, confirming before each write and verifying after. Writes to a Google Doc via a user-supplied OAuth token; no store credentials. Use when the user says "prepare handover docs", "create the mobile handover doc", "handover documentation for this app", or asks to document builds/signing/store/release for a client handover. Do NOT use for Expo projects (use prepare-handover-docs-expo), for non-mobile repos, or for writing marketing/App Store listing copy.
version: 1.0.0
trigger: /prepare-handover-docs
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion]
---

# prepare-handover-docs (bare React Native)

Builds a mobile-app **handover Google Doc**, one native tab at a time, filled from this
project and from a few things only the user knows. This skill is for **bare React
Native**. If the project is Expo (an `expo` dependency + `app.json`/`app.config` with an
`expo` key, and often no `ios/`/`android/` folders), stop and tell the user to run
`/prepare-handover-docs-expo` instead.

Load these as you go (they are the real content; this file is the flow):
`${CLAUDE_PLUGIN_ROOT}/references/interaction-protocol.md`,
`${CLAUDE_PLUGIN_ROOT}/references/detection-bare.md`,
`${CLAUDE_PLUGIN_ROOT}/references/tab-templates.md`,
`${CLAUDE_PLUGIN_ROOT}/references/release-tab-bare.md`,
`${CLAUDE_PLUGIN_ROOT}/references/spec-format.md`,
`${CLAUDE_PLUGIN_ROOT}/references/token-guide.md`,
`${CLAUDE_PLUGIN_ROOT}/references/drive-layout.md`.

## Hard rules

1. **Never put a secret value in a spec or the doc.** Only key names, public
   identifiers, keystore fingerprints, links, and vault pointers. Read env key names
   from `*.example`, never from `.env`. Never echo a keystore password, API token, or
   `.p8`.
2. **Never ask for anything the repo can answer.** Run detection first; ask the user only
   for what is genuinely outside the code (store status, build numbers, account owners,
   Drive links, Play App Signing on/off, signing model when ambiguous).
3. **Confirm before every write.** No tab is written to Google without an explicit
   confirmation for that specific tab. Follow the interaction protocol exactly.
4. **Use the real project name, detected — never a placeholder or an example's name.**
   Nothing in the output should be specific to any other project.
5. **Append-only engine, no tab-delete.** Editing a tab = the user deletes it in the
   Docs sidebar, then you regenerate. Tab titles must be unique.
6. **Verify the tail.** After writing, re-read the tab and confirm the last spec block's
   text is present. Never report success on an unverified tail.
7. **Never predict store approval.** Report status as observed ("Waiting for Review"),
   never "will pass".

## Run flow

Follow `interaction-protocol.md` for the exact stop-and-confirm cadence. In summary:

### Step 0 — Detect and set up

1. Confirm this is bare React Native (else route to the `-expo` skill).
2. Run detection (`detection-bare.md`): app display name, bundle id/package, versions,
   Firebase presence, env files, schemes/flavors, keystore. State branch/commit/dirty.
3. Confirm the **app display name** to use everywhere.
4. Show the default tabs — **Overview, Env, Firebase, App Store, Play Store, Release &
   Rollback** — and ask to **add/remove** any. Offer to drop Firebase if no config files
   were found.
5. Ask for the **target doc** (existing id, or have the user make a new empty doc and
   share edit access to the token identity) and the **OAuth token** (walk through
   `token-guide.md` if needed).

### Steps 1–6 — one tab each, in order: Env → Firebase → App Store → Play Store → Release & Rollback → Overview (last)

For each tab, per the protocol:

1. **Announce** what the tab includes — split into *auto from repo* vs *needs you*.
2. **Gather**: auto-discover from the repo; ask the user for the rest and for anything to
   add/remove.
3. **Draft** the spec to `docs/handover/specs/<tab>.json` in **this project** using the
   template in `tab-templates.md` (Release tab uses `release-tab-bare.md`). Run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_doc.py" --spec <path> --dry-run` and
   confirm "self-check PASSED". Show a **sign-off view** listing any `PENDING_*`.
4. **Stop for confirmation.**
5. **Write** (after checking the token is fresh, and after the duplicate-tab guard):
   ```
   SSL_CERT_FILE="$(python3 -m certifi 2>/dev/null || echo /etc/ssl/cert.pem)" \
   DOCS_TOKEN="<token>" \
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_doc.py" \
     --spec docs/handover/specs/<tab>.json --doc <docId>
   ```
   On `401`, ask for a fresh token and retry. On "Tab title … must be unique", have the
   user delete the existing tab and retry.
6. **Verify** the last block landed, then **stop** for the user to check the tab before
   the next one.

Compute keystore fingerprints only if the keystore file and password are available
(`keytool -list -v …`); otherwise ask the user for SHA-1/SHA-256. Screenshots (store
status) are optional `image` blocks — offer them on the App Store / Play Store steps.

## What this skill cannot do

- **It cannot change a store or a console.** Store status, account roles, and build
  numbers come from the user; every store-side action is theirs.
- **It cannot edit a tab in place** — delete + regenerate only.
- **It does not commit** the generated specs; that is the user's choice.
- **Bare React Native only.** Expo → `prepare-handover-docs-expo`. Other stacks are out
  of scope; say so rather than guessing.

## Before you write any tab

- [ ] Project detected; branch/commit/dirty stated; app name confirmed
- [ ] Tab list agreed (add/remove handled)
- [ ] Target doc id and a valid token in hand
- [ ] Spec dry-run passed; sign-off view shown; `PENDING_*` called out
- [ ] User confirmed this specific tab
- [ ] No secret value anywhere in the spec
- [ ] Duplicate-tab guard checked
- [ ] After write: last-block verify passed; user asked to review before next tab
