# Code-side checks

What the scanner establishes, how to read it, and where it stops. Everything here is
already in `findings.json` — this file explains the reasoning so you can judge the
output rather than repeat the work.

## The three-way privacy diff

An iOS app declares its privacy behaviour in three places that drift apart silently:

| Source | Where it lives | Read by |
|---|---|---|
| Privacy labels | App Store Connect only | screenshot (no API exists) |
| Privacy manifest | `PrivacyInfo.xcprivacy` in the repo | scanner |
| Actual behaviour | the SDKs the app ships | scanner |

The scanner settles legs two and three. You supply leg one from the App Privacy page.
All three must agree.

The classic failure: a manifest carrying `NSPrivacyTracking` = `false` and an empty
`NSPrivacyCollectedDataTypes`, while the listing declares tracking plus a dozen data
types and the app ships an SDK that reads the advertising identifier. Apple's
automated pre-review scan compares the binary against the declarations, so this is
found by machine, not by luck.

**Prove the negative before writing the finding.** `NSPrivacyTracking = false` is only
wrong if something actually tracks. Check the SDK inventory first. An app with
Crashlytics and nothing else is correctly declaring no tracking.

Read `signals.trackingSdks` as three separate buckets:

- **`idfa`** — reads an advertising identifier. Makes a `false` tracking declaration
  a real problem.
- **`analytics`** — first-party product analytics. Usually **not** tracking under
  Apple's definition, which turns on linking to third-party data for ads. Do not
  treat an analytics SDK alone as proof of tracking.
- **`diagnostics`** — crash and performance reporting. Not tracking.

## Permissions, both directions

**Declared but unused** — a usage-description key exists, nothing exercises it.
Data-minimisation problem under 5.1.1, and reviewers ask what it is for. Usually
MEDIUM. Evidence is the plist line plus a zero-hit search, which the validator
re-runs.

**Used but undeclared** — protected API called with no key present. iOS terminates the
app on the first call, so a reviewer hits it immediately. BLOCKER.

Two refinements that matter when judging these:

**Background location is a special case.** A declared
`NSLocationAlwaysAndWhenInUseUsageDescription` with no code requesting always-
authorisation is already a finding, but check `UIBackgroundModes` too. If it does not
contain `location`, nothing in the app *can* use background location, and the key is
simply unnecessary — a much cleaner recommendation than "review your usage". Also
read the string itself: copy promising "only while you are using the app" attached to
an Always key contradicts the key it is on, which is its own red flag.

**Write-only calendar access is not data collection.** `NSCalendarsWriteOnlyAccess-
UsageDescription` used to add a local reminder collects nothing — the event never
leaves the device, so no privacy label is owed. Declaring both the write-only key and
the legacy full-access key is correct practice for iOS 17+ with back-compatibility,
not a duplicate. Do not manufacture a finding here.

## Version alignment

Compared **between targets**, never against a configured expected value, so the check
works on a project it has never seen.

| Condition | Severity | Why |
|---|---|---|
| Extension `MARKETING_VERSION` ≠ app's | BLOCKER | fails upload validation before review |
| Two app configurations disagree | HIGH | which value ships depends on the scheme archived |
| `CURRENT_PROJECT_VERSION` differs across targets | LOW | Apple enforces the short version string, not this one |
| Android `versionName` ≠ iOS | MED | one release with two numbers; support and crash triage get ambiguous |

The listing's own version field is a fourth value, collected on page 06. All four must
agree, and the build number must exceed what has already been uploaded — a duplicate
build number is rejected at upload.

## Login wall

`signals.loginKinds` reports how a reviewer would have to sign in. `otpSms` is the
dangerous one: **a reviewer cannot receive an SMS.** Unless the demo number in App
Store Connect bypasses SMS on the backend, the reviewer cannot get in, and 2.1 makes
that a rejection.

This cannot be verified by any tool. It ends **attested** — the user confirms the test
credentials work end to end — and the review notes must explain the arrangement.
Guideline 2.1 is explicit about turning the backend service on.

## Region lock

Two or more independent signals pointing at one market is treated as a finding:
regional payment app hand-offs in `LSApplicationQueriesSchemes`, region-specific
payment SDKs, a single currency, a country-specific postal field.

The finding is about the *mismatch* with the territory count on page 03, not about
being single-market — which is a perfectly reasonable business choice. An app shipped
where checkout, delivery or address entry cannot work is incomplete in those
territories under 2.1, and thin under 4.2.

**This finding cascades.** Narrowing territories can retire EU-specific obligations
outright. Fix it before the compliance page, and re-check page 02 afterwards.

## Toolchain floor

The scanner reports the local Xcode version and deployment targets but **cannot judge
them** — the current minimum comes from Upcoming Requirements at run time. Compare
them yourself, and do not confuse the two: `IPHONEOS_DEPLOYMENT_TARGET` is the oldest
iOS the app runs on and is unrelated to the SDK floor for uploads.

If iOS builds run in CI, check the runner pins an Xcode version. A workflow with no
pin passes until the day the runner image moves.

## Reading `notChecked`

Not-checked is not a soft pass. It means the check could not be settled from a
repository, and each entry carries its reason. A page that is largely not-checked is
an honest result — say so plainly rather than padding it with findings about wiring
dressed up as findings about outcomes.
