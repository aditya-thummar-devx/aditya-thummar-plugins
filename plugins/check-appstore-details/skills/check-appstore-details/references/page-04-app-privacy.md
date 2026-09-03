# Page 04 — App Privacy

The highest-value page in the audit, and the one with no API at all. This is where the
third leg of the three-way privacy diff comes from — the other two legs are already in
`findings.json`.

Apple's automated pre-review scan compares the shipped binary against these
declarations, so a mismatch here is found by machine rather than by a reviewer's
attention.

## What to ask for

> App Store Connect → your app → **App Privacy**. Screenshot the Product Page Preview
> (the three columns: Data Used to Track You, Data Linked to You, Data Not Linked to
> You), then the Data Types section below it.

The Data Types section is long. Ask for **as many screenshots as it takes**, and say
so up front — this is the one page where several images are expected. If a data type's
purposes are collapsed, ask for the summary line rather than every expansion.

Also capture the **Privacy Policy URL** at the top of the page.

## Checks

| Check | Pass criteria |
|---|---|
| Tracking declaration agrees with the privacy manifest | Both say tracking, or both say none |
| Tracking declaration agrees with the shipped SDKs | An advertising-identifier SDK implies tracking |
| Device ID marked as tracking, when an ad SDK is present | Advertising identifier use is tracking under Apple's definition |
| Declared data types cover what the code actually sends | Nothing sent that is undeclared |
| Privacy Policy URL is present and live | Reachable, and not a placeholder page |
| Data types not collected are not over-declared | Over-declaring is safer than under, but should still be deliberate |

## How to verify

**Start from the manifest finding.** `findings.json` already reports
`NSPrivacyTracking` and the collected-data-type count from `PrivacyInfo.xcprivacy`,
plus the SDK inventory. Lay the labels beside them:

| | Says |
|---|---|
| Privacy labels (this page) | what you just read |
| `PrivacyInfo.xcprivacy` | in `findings.json` |
| Shipped SDKs | in `findings.json` |

All three must agree. Quote the actual values from all three when reporting a
mismatch — hard rule 4.

**Device ID and the advertising identifier.** If the app ships an SDK from the `idfa`
bucket and prompts for tracking authorisation, then Device ID is being used for
tracking, and Apple expects it under **Data Used to Track You**. A listing declaring
Device ID as merely "linked to you, app functionality" while the app reads the
advertising identifier for ad measurement is the exact mismatch the automated scan
looks for. Cite 5.1.2 with a quote.

**Analytics is not automatically tracking.** Apple's definition turns on linking user
data with third-party data for targeted advertising or sharing with a data broker.
First-party product analytics and crash reporting usually are not tracking. Read the
SDK buckets in `findings.json` — `idfa` implies tracking, `analytics` and
`diagnostics` on their own do not.

**Privacy Policy URL.** `check-urls.py` tests reachability. 5.1.1(i) requires the link
in the metadata field *and* somewhere accessible inside the app — check the code for
an in-app privacy link too, not just this field.

**Data types versus what the code sends.** Where `findings.json` shows an SDK
transmitting hashed email, phone or name, those belong in Contact Info and should be
marked linked. Where it shows purchase events going to an ad platform, Purchases
belongs under tracking.

## Common false positives

- **Write-only calendar access collects nothing.** Adding a local reminder that never
  leaves the device owes no privacy label. Apple's data types have no "Calendar"
  entry for this reason. Do not invent one.
- **Over-declaration is not a rejection risk.** Declaring a data type the app does not
  collect is conservative and harmless. Mention it as tidy-up at LOW, never as a
  blocker.
- **Precise Location for a one-off address autofill is legitimately "App Functionality,
  not linked".** Using location to fill a postcode field or find a nearby store does
  not make it tracking, and does not require linking to identity.
- **Hashing does not remove the obligation.** SHA-256 hashed email sent to an ad
  platform is still Contact Info, still linked, still tracking. Do not accept
  "it's hashed" as a reason it need not be declared.
- **An ATT prompt on its own does not prove tracking is declared correctly.** It
  proves the app *asks*. What matters is whether the labels match what happens after
  the user agrees.
- **A privacy policy returning 403 to an automated request may still be live.** Some
  hosts block non-browser user agents. Report the status code and ask the user to
  confirm in a browser rather than declaring the URL dead.

## Cannot be determined from this page

- **Anything, without a screenshot.** There is no API for privacy labels — confirmed
  against the App Store Connect OpenAPI spec, which contains zero `appDataUsage`
  paths. If the user will not or cannot send this page, every check here becomes
  not-checked, and the three-way diff collapses to a two-way one. Say so plainly.
- Whether the privacy policy *text* accurately describes the practices — that is a
  document review, not a listing check
- Per-purpose detail when the page's sections are collapsed
- Whether a third-party SDK collects something its documentation does not mention
