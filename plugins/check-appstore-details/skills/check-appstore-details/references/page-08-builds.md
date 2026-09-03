# Page 08 — Builds

Optional page. Ask for it only when the version and build numbers need settling —
typically when `findings.json` reported version drift, or when the user is about to
upload a new build and needs to know which number is free.

Skip it entirely for an audit of an already-attached, already-processed build.

## What to ask for

> App Store Connect → your app → **TestFlight** → iOS Builds, or the Build section of
> the version page. Screenshot the list showing build numbers, versions and status.

## Checks

| Check | Pass criteria |
|---|---|
| The next build number is unused | Higher than every number already uploaded for this version |
| The attached build carries the expected version | Matches the app target's `MARKETING_VERSION` |
| The attached build has finished processing | Not stuck in Processing or Invalid |
| No build is missing its compliance answer | Export-compliance prompts resolved |

## How to verify

**Build number availability.** A duplicate build number is rejected at upload, before
review, and it is a pointless round trip. Compare the highest number visible against
`CURRENT_PROJECT_VERSION` in `findings.json`.

Two things worth being precise about:

- The build number must be unique **per version string**, not globally. Version `1.0`
  build `7` and version `1.1` build `1` coexist fine.
- The version string and build number are different fields with different rules.
  `CFBundleShortVersionString` (`MARKETING_VERSION`) is what the store shows and what
  Apple enforces between an app and its extensions. `CFBundleVersion`
  (`CURRENT_PROJECT_VERSION`) is the upload discriminator. Do not conflate them; the
  advice differs.

**Version of the attached build.** If the attached build shows a different version
string from the listing's version field, that is the mismatch page 06 flagged, now
confirmed from the other direction. The uploaded binary's version is frozen — it
cannot be changed without a new build — so the listing field is what moves.

**Processing state.** A build in Processing is pending, not a finding; it usually
clears within half an hour. A build marked Invalid *is* a finding, and the reason
arrives by email rather than appearing here — ask the user to check.

## Common false positives

- **A gap in build numbers is not a problem.** Skipping from 4 to 7 is normal; failed
  uploads and abandoned archives consume numbers.
- **A non-sequential build number is fine.** Nothing requires increments of one.
- **Old builds shown as Expired are normal.** TestFlight builds expire after 90 days
  and expiry says nothing about the App Store version.
- **A UAT or staging flavour with its own build numbers is not drift** if it is a
  separate bundle ID. Check `findings.json` — several configurations sharing one bundle
  ID with different build numbers is worth a mention; genuinely separate apps are not.
- **"Processing" is not "missing".** Record pending, not failed.

## Cannot be determined from this page

- **Complete build history.** Only what is on screen. The "is this number free" check
  is therefore approximate — say so rather than implying certainty.
- Why a build was marked Invalid — that reason is emailed, not displayed
- Whether a build was uploaded from the current commit — nothing on the page links a
  build to a git SHA
- Whether an older build is still in review
