# Release & Rollback template — bare React Native

Build the `Release & Rollback` tab from the project's own `package.json` / Gradle
scripts and the Xcode archive flow. Read the actual script names from `package.json`
(`grep '"scripts"'`); the names below are the common shape — use whatever the repo
defines. Note when scripts embed macOS-only commands (`open`, `killall`) and say so.

## Sections (engine blocks)

- `h1` "Release & Rollback"; `para` intro (produce/ship each platform locally; iOS is a
  manual Xcode archive; note macOS-only scripts if present).

- **label** "Prerequisites (local build environment)" → `bullet`s: toolchain (Node from
  `.nvmrc`, yarn/npm, Ruby+bundler, CocoaPods, Xcode, Android SDK+JDK); config files in
  place (`.env*` — see Env tab; `google-services.json` at `android/app/`,
  `GoogleService-Info.plist` at `ios/` — see Firebase tab); Android release signing
  (`android/local.properties` `RELEASE_*` + keystore at `android/app/` — see PlayStore
  tab); install deps (`yarn install && <pod install script>`).

- **label** "Android — production release build" → numbered `bullet`s:
  1. Bump `versionCode` (must increase) + `versionName` in `android/app/build.gradle`
     (manual — no auto bump).
  2. Build the Play bundle (AAB): the repo's `bundle*ProductionRelease` script, with a
     `detail` for the output path `android/app/build/outputs/bundle/productionRelease/*.aab`.
  3. Optional installable APK: the repo's `assemble*ProductionRelease`/qa-apk script.
  4. Upload the `.aab` to Play Console → Production; keep `mapping.txt` for crash
     de-obfuscation.

- **label** "Android — QA / staging build" → `bullet` for the QA/UAT APK script.

- **label** "iOS — production release (manual Xcode archive)" → `bullet`s:
  1. Prereqs (`.env`, pods installed, Xcode signed into the account with the team).
  2. Bump `MARKETING_VERSION` + `CURRENT_PROJECT_VERSION` in Xcode (build # must
     increase).
  3. Open `ios/<workspace>.xcworkspace`, select the production scheme, Release, Any iOS
     Device.
  4. Product → Archive → Distribute App → App Store Connect (or Export for an IPA).

- **label** "Rollback" → `bullet`s:
  - Android: can't reuse/lower a versionCode → **roll forward** with a higher-code fix;
    halt the staged rollout in Play Console to stop distribution.
  - iOS: can't revert a live version → submit a new build; pause phased release; request
    expedited review for a critical fix.
  - OTA: if no CodePush/OTA is wired, say so — every change ships as a new store build.
    (If an OTA library **is** present and configured, document its rollback instead.)

- **label** "Version rules (avoid store rejection)" → `bullet`s: Android versionCode must
  strictly increase; iOS build number must increase on every upload.
