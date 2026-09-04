---
name: prepare-handover-docs-expo
description: Build a client-handover Google Doc for an Expo / EAS mobile app — one native tab per area (env config, Firebase, App Store, Play Store, release & rollback via EAS, and an overview). Detects the current Expo project (app.json / app.config, eas.json) and fills every tab from the repo plus the few things only the user knows, one step at a time, confirming before each write and verifying after. Writes to a Google Doc via a user-supplied OAuth token; no store credentials. Use when the user says "prepare handover docs" (and the project uses Expo/EAS), "create the Expo handover doc", or asks to document builds/signing/store/release for an Expo app handover. Do NOT use for bare React Native (use prepare-handover-docs), for non-mobile repos, or for writing marketing copy.
version: 1.0.0
trigger: /prepare-handover-docs-expo
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion]
---

# prepare-handover-docs-expo (Expo / EAS)

Builds a mobile-app **handover Google Doc**, one native tab at a time, filled from this
Expo project and from a few things only the user knows. This skill is for **Expo / EAS**.
If the project is bare React Native (native `ios/`+`android/` folders, no `expo` key in
the app config), stop and tell the user to run `/prepare-handover-docs` instead.

Load these as you go: `${CLAUDE_PLUGIN_ROOT}/references/interaction-protocol.md`,
`${CLAUDE_PLUGIN_ROOT}/references/detection-expo.md`,
`${CLAUDE_PLUGIN_ROOT}/references/tab-templates.md`,
`${CLAUDE_PLUGIN_ROOT}/references/release-tab-expo.md`,
`${CLAUDE_PLUGIN_ROOT}/references/spec-format.md`,
`${CLAUDE_PLUGIN_ROOT}/references/token-guide.md`,
`${CLAUDE_PLUGIN_ROOT}/references/drive-layout.md`.

## Hard rules

1. **Never put a secret value in a spec or the doc.** Only key names, public
   identifiers, keystore fingerprints, links, and vault pointers. Read env key names
   from `*.example`, never from `.env`. Never echo a keystore password, API token, or
   `.p8`.
2. **Never ask for anything the repo can answer.** Run detection first (resolve dynamic
   config with `npx expo config --json` when needed); ask the user only for what is
   outside the code (store status, build numbers, account owners, Drive links, whether
   credentials are EAS-managed, Play App Signing on/off).
3. **Confirm before every write.** No tab is written to Google without an explicit
   confirmation for that specific tab. Follow the interaction protocol exactly.
4. **Use the real project name, detected — never a placeholder or an example's name.**
5. **Append-only engine, no tab-delete.** Editing a tab = the user deletes it in the
   Docs sidebar, then you regenerate. Tab titles must be unique.
6. **Verify the tail.** After writing, re-read the tab and confirm the last spec block's
   text is present. Never report success on an unverified tail.
7. **Never predict store approval.** Report status as observed.

## Run flow

Follow `interaction-protocol.md` for the exact stop-and-confirm cadence. In summary:

### Step 0 — Detect and set up

1. Confirm this is Expo (else route to the bare skill). If the project was prebuilt and
   has native folders, use `detection-bare.md` for those native bits.
2. Run detection (`detection-expo.md`): app name, bundle id/package, versions from the
   app config; `eas.json` build/submit profiles; Firebase via `googleServicesFile`;
   env/EAS config; credentials location (EAS-managed vs local). State branch/commit/dirty.
3. Confirm the **app display name** to use everywhere.
4. Show the default tabs — **Overview, Env, Firebase, App Store, Play Store, Release &
   Rollback** — and ask to **add/remove** any. Offer to drop Firebase if no config is
   referenced.
5. Ask for the **target doc** and the **OAuth token** (walk through `token-guide.md`).

### Steps 1–6 — one tab each, in order: Env → Firebase → App Store → Play Store → Release & Rollback → Overview (last)

For each tab, per the protocol:

1. **Announce** what the tab includes — *auto from repo* vs *needs you*.
2. **Gather**: auto-discover; ask for the rest and for anything to add/remove.
3. **Draft** the spec to `docs/handover/specs/<tab>.json` using `tab-templates.md` (the
   Release tab uses `release-tab-expo.md` — EAS build/submit, and EAS Update for OTA if
   configured). Dry-run the engine and show a **sign-off view** with any `PENDING_*`.
4. **Stop for confirmation.**
5. **Write** (token fresh + duplicate-tab guard first):
   ```
   SSL_CERT_FILE="$(python3 -m certifi 2>/dev/null || echo /etc/ssl/cert.pem)" \
   DOCS_TOKEN="<token>" \
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_doc.py" \
     --spec docs/handover/specs/<tab>.json --doc <docId>
   ```
   On `401`, ask for a fresh token. On a unique-title error, have the user delete the
   existing tab and retry.
6. **Verify** the last block landed, then **stop** for the user to check before the next.

For signing: if credentials are **EAS-managed**, document that (`eas credentials`) rather
than fingerprints; if a local keystore + password are available, compute SHA-1/SHA-256
with `keytool`; otherwise ask. Screenshots are optional `image` blocks on the store steps.

## What this skill cannot do

- **It cannot change a store, console, or EAS.** Status, roles, and build numbers come
  from the user.
- **It cannot edit a tab in place** — delete + regenerate only.
- **It does not commit** the generated specs.
- **Expo / EAS only.** Bare React Native → `prepare-handover-docs`. Other stacks are out
  of scope.

## Before you write any tab

- [ ] Expo confirmed; branch/commit/dirty stated; app name confirmed
- [ ] Tab list agreed (add/remove handled)
- [ ] Target doc id and a valid token in hand
- [ ] Spec dry-run passed; sign-off view shown; `PENDING_*` called out
- [ ] User confirmed this specific tab
- [ ] No secret value anywhere in the spec
- [ ] Duplicate-tab guard checked
- [ ] After write: last-block verify passed; user asked to review before next tab
