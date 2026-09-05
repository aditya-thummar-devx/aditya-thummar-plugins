# Detection — bare React Native

Where to read each fact from a bare React Native project. Read what you can; for
anything missing or ambiguous, ask the user rather than guessing. Prefer redacted
example files over real ones. Never read secret values into a spec.

## App identity & name

- **App display name** (priority order, confirm with user):
  `app.json` / `app.config.(js|ts|json)` `displayName` → iOS `ios/*/Info.plist`
  `CFBundleDisplayName` (fall back to `CFBundleName`) → `package.json` `name`.
- **iOS bundle id**: `PRODUCT_BUNDLE_IDENTIFIER` in `ios/*.xcodeproj/project.pbxproj`
  (there may be extra targets, e.g. a notification service — list them).
- **Android package / applicationId**: `applicationId` in `android/app/build.gradle`
  (and `namespace`).
- **Apple Team ID**: `DEVELOPMENT_TEAM` in `project.pbxproj`.
- **Xcode schemes**: `ios/*.xcodeproj/xcshareddata/xcschemes/*.xcscheme` (names +
  Release/Debug config). **Android flavors**: `productFlavors { }` in
  `android/app/build.gradle`.

## Versions

- **iOS**: `MARKETING_VERSION` and `CURRENT_PROJECT_VERSION` in `project.pbxproj`.
- **Android**: `versionName` and `versionCode` in `android/app/build.gradle`
  (`defaultConfig`).

## Env files

- Glob `.env*` at the project root (e.g. `.env`, `.env.uat`, `.env.staging`,
  `.env.production`) and their `*.example` counterparts.
- **Read key names + comments from the `*.example` files** (`grep -oE '^[A-Z0-9_]+='`).
  If no example exists, ask the user for the key list — do not read `.env`.
- **Flavor → env-file mapping**: `project.ext.envConfigFiles` in
  `android/app/build.gradle` (react-native-config), and the `ENVFILE=...` usage in
  `package.json` scripts for iOS schemes.
- Note the runtime accessor if present (e.g. `getConfig` / react-native-config) and any
  Remote Config override layer.

## Firebase

- **Android**: `android/app/google-services.json` → `project_info.project_id`,
  `project_number`, `storage_bucket`, `client[].client_info.mobilesdk_app_id`,
  `package_name`.
- **iOS**: `ios/**/GoogleService-Info.plist` → `PROJECT_ID`, `GCM_SENDER_ID`,
  `GOOGLE_APP_ID`, `BUNDLE_ID`, `STORAGE_BUCKET`.
- **Modules in use**: grep `package.json` for `@react-native-firebase/*`
  (analytics, crashlytics, perf, remote-config, messaging, …).
- If neither config file exists, the project likely has no Firebase — offer to drop the
  Firebase tab.
- **Do not** put the `api_key` / `API_KEY` from these files in the doc; those files go to
  the Drive folder.

## Android signing / keystore

- Look for a keystore: `android/app/*.jks` or `*.keystore`, and `RELEASE_*` keys in
  `android/local.properties` (`RELEASE_STORE_FILE`, `RELEASE_KEY_ALIAS`, …).
- **Fingerprints** (safe to document): if the keystore file **and** its password are
  available, compute with
  `keytool -list -v -keystore <file> -alias <alias> -storepass <pw>` and take the
  `SHA1:` and `SHA256:` lines, alias, algorithm, and validity. **Never** put the
  password in the doc.
- If the keystore or password is not available, **ask** the user for the SHA-1 / SHA-256
  (Play Console → Setup → App signing shows both).
- Whether **Play App Signing** is enabled (Google holds the signing key; the local
  keystore is the upload key) is a Play Console fact — **ask**.

## Push (APNs / FCM)

- FCM comes with the Firebase config above.
- APNs: whether an `ios/**/NotificationService` extension exists; the APNs Key ID, Team
  ID, and `.p8` location are **asked** (the Key ID also shows in Firebase → Project
  settings → Cloud Messaging).

## Store & accounts (always ask)

App Store Connect app id + status, TestFlight build numbers, Apple account holder,
Play Console owner + release status/track, and all account roles are **not** in the
repo. Ask for them, and offer to embed a store-status screenshot.

## Release commands

Read build scripts from `package.json` (e.g. Gradle `assemble*`/`bundle*` wrappers, and
`react-native run-*`). The Release & Rollback tab uses these — see `release-tab-bare.md`.
