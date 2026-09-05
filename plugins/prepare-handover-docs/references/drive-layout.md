# Recommended handover Drive layout

The doc links to files that must not live in the repo (filled env files, Firebase
config, signing keys, builds). Keep them in one **area-based** Drive folder, shared to
the client only. Guide the user to create this structure and give you each sub-folder's
share link at the matching step.

```
<App> Handover/                 (root — shared to the client only)
├── <Handover Google Doc>       the doc this skill builds
├── ENVs/                       .env and every other .env.<variant> the project uses
├── Firebase/                   google-services.json, GoogleService-Info.plist
├── App Store - iOS/            APNs auth key  AuthKey_<KeyID>.p8
└── Play Store - Android/       upload keystore (.jks), keystore credentials, builds/ (AAB/APK)
```

## Which link goes on which tab

| Tab | Links to | Contents |
| --- | --- | --- |
| Env | `ENVs/` | the filled env files |
| Firebase | `Firebase/` | the two config files |
| App Store | `App Store - iOS/` | the APNs `.p8` |
| Play Store | `Play Store - Android/` | keystore `.jks`, credentials file, `builds/` |

## Rules to state to the user

- **Restrict sharing to the client** (specific people), never "anyone with the link",
  never a broad org share.
- **Secrets live here, not in the doc.** Keystore passwords go in a small
  `keystore-credentials.txt` inside the Play Store folder (or a password manager), and
  env secret values stay inside the filled env files here.
- **Show links as raw URLs** in the doc (the `figline` text equals the url), so the
  reader sees exactly where they're going.
- The APNs `.p8` can be downloaded from Apple **only once** — if it was never saved, the
  key must be revoked and re-created in the Apple Developer portal, then re-uploaded to
  Firebase, and the new Key ID recorded.
