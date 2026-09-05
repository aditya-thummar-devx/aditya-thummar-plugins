# Detection — Expo / EAS

Where to read each fact from an Expo project. Managed Expo projects often have **no
`ios/` or `android/` folders** (they are generated at build time by prebuild/EAS), so
identity and versions come from the app config, and release comes from EAS. If the
project has been prebuilt (bare workflow with `ios/`+`android/`), fall back to the
bare-RN detection for the native bits.

## Detect Expo first

Signals: `expo` in `package.json` dependencies, an `app.json`/`app.config.(js|ts)` with
an `expo` key, and/or an `eas.json`. If these are absent, this is not an Expo project —
use the bare skill instead.

## App identity & name

Read from `app.json` or `app.config.(js|ts)` under the `expo` key (evaluate
`app.config.js` output if the config is dynamic — `npx expo config --json` gives the
resolved config):

- **App display name**: `expo.name` (confirm with user).
- **iOS bundle id**: `expo.ios.bundleIdentifier`.
- **Android package**: `expo.android.package`.
- **Apple Team ID**: `expo.ios.appleTeamId` if set, else from `eas.json`
  (`submit.<profile>.ios.appleTeamId`) or ask.

## Versions

- **Marketing version**: `expo.version`.
- **iOS build number**: `expo.ios.buildNumber`.
- **Android versionCode**: `expo.android.versionCode`.
- If `expo.runtimeVersion` or the `expo-updates` config is present, note the OTA/runtime
  version policy (see the release tab — EAS Update may be the OTA path here, unlike bare).

## Env / config

- Expo apps typically read config via `expo.extra`, `app.config.js` reading
  `process.env.*`, or **EAS environment variables / secrets** (`eas env` / the
  `env` blocks in `eas.json` build profiles).
- Still glob `.env*` + `*.example` at the root and read key **names** from the examples.
- Document where production values come from: `.env` baked at build, `eas.json` `env`,
  or EAS secrets. Ask if unclear. Never read secret values.

## Firebase

- Expo usually references the Firebase config files via config:
  `expo.ios.googleServicesFile` and `expo.android.googleServicesFile` in the app config.
  Read those paths, then read the referenced `GoogleService-Info.plist` /
  `google-services.json` for project id/number/bucket/app-ids (same fields as bare).
- Firebase modules: `@react-native-firebase/*` in `package.json`, or the
  `@react-native-firebase/app` config plugin in the app config.
- If no Firebase config is referenced, offer to drop the Firebase tab.

## Signing / keystore

- With **EAS Build**, credentials are usually managed by EAS (`eas credentials`) — the
  Android upload keystore and iOS distribution cert/profile can live on EAS servers, not
  in the repo. Document *where* they live (EAS-managed vs a local keystore) — **ask**.
- If a local Android keystore + password are available, compute SHA-1/SHA-256 with
  `keytool` (as in bare). Otherwise **ask** for the fingerprints (Play Console → App
  signing) or note they are EAS-managed (`eas credentials`).
- Play App Signing on/off is a Play Console fact — **ask**.

## Push (APNs / FCM)

- FCM via the Firebase config. APNs Key ID / Team ID / `.p8` are **asked** (or
  EAS-managed via `eas credentials`).

## Store & accounts (always ask)

Same as bare — App Store Connect app id + status, TestFlight builds, Apple account
holder, Play Console owner + release status, account roles. Ask; offer a screenshot.

## Release commands

Expo uses **EAS**, not local Gradle/Xcode: `eas build --platform <ios|android> --profile
production`, then `eas submit`. Read build profiles from `eas.json`. OTA, if enabled, is
`eas update`. The Release & Rollback tab uses these — see `release-tab-expo.md`.
