# Release & Rollback template — Expo / EAS

Build the `Release & Rollback` tab from the project's `eas.json` build/submit profiles
and Expo's app config. Read the actual profile names from `eas.json` (`build.*`,
`submit.*`); the names below are the common shape — use whatever the repo defines.

## Sections (engine blocks)

- `h1` "Release & Rollback"; `para` intro (builds run on EAS, not local Gradle/Xcode;
  submissions via `eas submit`).

- **label** "Prerequisites" → `bullet`s: `eas-cli` installed and logged in
  (`eas login`); config files referenced by the app config in place (env — see Env tab;
  Firebase `googleServicesFile` paths — see Firebase tab); credentials available
  (EAS-managed via `eas credentials`, or provided — see PlayStore/AppStore tabs); an
  `eas.json` with a production build profile.

- **label** "Version management" → `bullet`s: bump `expo.version` (marketing) and the
  platform build numbers (`expo.ios.buildNumber`, `expo.android.versionCode`) in the app
  config — or, if `eas.json` sets `"autoIncrement": true` for the profile, note that EAS
  bumps them automatically. Build numbers/codes must increase per store upload.

- **label** "Build (EAS)" → `bullet`s:
  - Android AAB: `eas build --platform android --profile production`.
  - iOS: `eas build --platform ios --profile production`.
  - `detail`: artifacts are downloadable from the EAS build page; keep the Android
    `mapping`/sourcemaps for crash de-obfuscation.

- **label** "Submit to the stores" → `bullet`s:
  - `eas submit --platform android --profile production` (or upload the AAB to Play
    Console → Production).
  - `eas submit --platform ios --profile production` (or upload via Transporter/Xcode).

- **label** "OTA updates (EAS Update)" → if `expo-updates` / EAS Update is configured
  (check `expo.updates` + `runtimeVersion` and `eas.json`): `eas update --branch
  <channel>` ships JS-only changes over the air; roll back by republishing a previous
  update to that branch (`eas update --branch <channel> --republish` / roll a prior
  update forward). If EAS Update is **not** configured, say every change ships as a new
  store build.

- **label** "Rollback" → `bullet`s:
  - JS-only regression with EAS Update: republish the previous good update to the channel
    (fast, no store review).
  - Native regression: build + submit a new binary with a higher build number/code;
    Android — halt the staged rollout and roll forward; iOS — new build / pause phased
    release / expedited review.

- **label** "Version rules" → `bullet`s: Android versionCode strictly increases; iOS
  build number increases per upload; an EAS Update must target a matching
  `runtimeVersion`.
