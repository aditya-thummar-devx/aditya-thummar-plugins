# Tab templates (generic, placeholder-driven)

The content shape for each tab. Fill placeholders from detection (see `detection-*.md`)
and from user answers. Everything here is stack-neutral except the Release & Rollback
tab, which has its own file per variant. Use the engine block types in `spec-format.md`.

Conventions:
- `<APP>` = the confirmed app display name; `<PKG>` = bundle id / package.
- Links are `figline` blocks whose `text` **equals** the `url` (raw clickable URL).
- Matrices are nested `bullet`s (level 0 header, level 1 rows) — there is no table type.
- Anything the user must still supply is a literal `PENDING_<THING>` in the draft; the
  sign-off view lists every `PENDING_*`.
- Never emit a secret value. Credentials are named and pointed at the Drive folder/vault.

Fixed tab order: **Env → Firebase → App Store → Play Store → Release & Rollback →
Overview (last)**. Tab titles: `Env Details`, `Firebase Details`, `AppStore Details`,
`PlayStore Details`, `Release & Rollback`, `Overview`.

---

## Env Details

- `h1` "Environment Configuration"; `para` one-line intro (how config is read; RC
  override layer if present).
- **label** "Environment files" → `para` (files are gitignored; filled copies in Drive;
  redacted `*.example` in repo) → one `bullet` per detected `.env*` variant.
- **label** "Download the filled files" → `figline` to the `ENVs/` Drive folder →
  `detail` naming the files inside.
- **label** "Where to place them" → `bullet` "project root" + `detail` per file path →
  `bullet` "selected by flavor/scheme" + `detail` lines for the mapping (from detection).
- **label** "What the env file contains" → `para` (names from `*.example`; values only in
  Drive; credentials marked) → grouped keys: a level-0 `bullet` per group (Environment
  selector, Endpoints & URLs, Credentials, Caching, Feature/Update gates, Security, …)
  with level-1 `bullet`s "KEY — purpose." Mark secrets "(credential)".
- If a Remote Config / live-override layer exists: **label** "Remote Config" → `para`
  explaining override precedence, and list any keys delivered only via RC (names only).

## Firebase Details

- `h1` "Firebase"; `para` intro (one project powers both platforms; services list).
- **label** "Firebase project" → level-0 `bullet`s: Project ID, Project number / Sender
  ID, Storage bucket, iOS app id (+ bundle), Android app id (+ package); a `bullet`
  "Owners:" with level-1 rows `PENDING_OWNER` (ask); `figline` to the Firebase console
  `https://console.firebase.google.com/project/<projectId>`.
- **label** "Config files" → `para` (gitignored; embed API key → Drive only) → `bullet`
  `google-services.json -> android/app/`, `bullet` `GoogleService-Info.plist -> ios/` →
  `figline` to the `Firebase/` Drive folder.
- **label** "Firebase services in use" → one `bullet` per detected module.
- **label** "Push notifications — APNs & FCM" → `bullet` Android (FCM via config) →
  `bullet` iOS (APNs `.p8` uploaded to Firebase) with level-1 `bullet`s: `APNs Key ID:
  PENDING_APNS_KEY_ID`, `Apple Team ID: <team>`, `Firebase project: <projectId>`, and a
  `figline` to the APNs `.p8` Drive folder → `bullet` noting a NotificationService
  extension if detected.
- If a Remote Config layer exists: **label** "Remote Config" → `para` + `figline`
  console `.../config`, and list RC-only keys (names). This is where env's RC-only keys
  are documented.

## AppStore Details

- `h1` "App Store (iOS)"; `para` intro (identity, ownership, signing, status; build
  procedure in Release & Rollback tab).
- **label** "App identity" → `bullet`s: App name `<APP>`, Apple ID `PENDING_ASC_APP_ID`,
  Bundle ID `<PKG>` (+ extensions), Apple Team ID `<team>`, Current version (from
  detection) → `figline` App Store Connect `https://appstoreconnect.apple.com/apps/<id>`
  and `figline` listing `https://apps.apple.com/app/id<id>`.
- **label** "Apple account & ownership" → `bullet`s: account holder `PENDING_HOLDER`,
  app lives under it, the agency/vendor user access is revocable via Users and Access. (ask)
- **label** "Signing, certificates & profiles" → `bullet`s describing the detected
  signing model (automatic vs manual; team) and the transfer mechanism (client owns the
  account → certs/profiles live in it; control = Users and Access; no `.p12` handoff if
  account-owned). Gather, do not assume.
- **label** "Builds & submission status" → `bullet`s: how iOS builds are produced
  (Release & Rollback tab), TestFlight build(s) `PENDING_TF_BUILD`, App Store status
  `PENDING_APPSTORE_STATUS`, distribution note. Optional `image` screenshot of the
  status.

## PlayStore Details

- `h1` "Play Store (Android)"; `para` intro.
- **label** "App identity" → `bullet`s: Package `<PKG>`, Current version (detection) →
  `figline` Play Console `https://play.google.com/console` and `figline` listing
  `https://play.google.com/store/apps/details?id=<PKG>`.
- **label** "Play account & ownership" → `bullet`s: developer account `PENDING_PLAY_OWNER`,
  agency access role (revocable via Users and permissions). (ask)
- **label** "Signing & keystore" → `bullet` Play App Signing on/off `PENDING_PAS`
  (implications) → `bullet` "Upload keystore details:" with level-1 rows: File, Alias,
  Algorithm/created/validity, `SHA-1: <fp>`, `SHA-256: <fp>` (from keytool or asked) →
  `figline` to the keystore Drive folder → `bullet` "credentials in the locked folder /
  vault — NOT in this document" → `bullet` local-build usage (keystore at `android/app/`,
  creds in `android/local.properties`).
- **label** "Build & release" → `bullet` how Android builds are produced (Release &
  Rollback tab) → `figline` to the builds Drive folder → `bullet` "Play release status:"
  with level-1 rows `PENDING_PLAY_STATUS`. Optional `image` screenshot.

## Overview (built last)

- `h1` "<APP> Mobile App Handover — Overview"; `para` what this doc is and who it's for.
- **label** "Tabs in this document" → one `bullet` per tab actually created, with a
  one-line description.
- **label** "App at a glance" → `bullet`s: App name, bundle/package, iOS version,
  Android version.
- **label** "Accounts & ownership" → the matrix as nested bullets: level-0 per account
  (Apple / Play / Firebase), level-1 owner + agency-role rows.
- **label** "Current store status" → `bullet`s summarizing App Store + Play status
  (as of today's date).
- **label** "Handover resources" → `para` + `figline` to the Drive root folder.
- **label** "A note on secrets" → `para`: no secret values in this document; credentials
  in the locked Drive folder / password manager.
