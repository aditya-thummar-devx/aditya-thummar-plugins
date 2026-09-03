# Page 03 — Pricing and Availability

Where the app is sold, and on what hardware. This page carries the single most common
serious mismatch: an app shipped worldwide whose code only works in one country.

**Run this page early.** Its outcome decides whether page 02's EU obligations apply.

## What to ask for

> App Store Connect → your app → **Pricing and Availability**. Screenshot the whole
> page, including the Apple Silicon Mac and Vision Pro sections and App Distribution
> Methods further down.

Ask for the **territory count** as it appears, and the **base country**.

## Checks

| Check | Pass criteria |
|---|---|
| Territory count is consistent with what the code supports | No large territory count against single-market code |
| Base country matches the code's currency | Base territory and the currency in the code agree |
| Apple Silicon Mac availability is deliberate | Off, or on and actually tested on a Mac |
| Vision Pro availability is deliberate | Off, or on and actually tested |
| Volume purchase / education pricing is deliberate | Off unless the app is genuinely sold to institutions |
| Distribution method is correct | Public for a consumer app; Private only for a custom enterprise app |

## How to verify

**Territory scope versus code reach.** This is the finding that matters. Read the
region signals in `findings.json`: regional payment app hand-offs, region-specific
payment SDKs, a single currency, a country-specific postal field. Two or more
independent signals pointing at one market, against a territory count in the dozens or
hundreds, means users in most of those territories cannot complete a purchase.

Cite **2.1 App Completeness** — a reviewer in an unsupported territory hits a dead
checkout — and **4.2 Minimum Functionality** for what remains usable there. Quote both.

Two legitimate resolutions, and it is the user's business decision which:

1. **Narrow the territories** to what the code serves. Usually correct, and it also
   retires the DSA obligation on page 02 if the EU drops out.
2. **Keep the territories** and accept the risk knowingly, ideally with review notes
   explaining how a reviewer should test.

Say both. Do not present narrowing as the only option.

**Base country against currency.** The base territory should be the market the app
actually prices in. A base of one country while the code hard-codes another currency
is a genuine inconsistency worth a question.

**The three toggles.** Apple Silicon Mac, Vision Pro and volume purchase are all
enabled by a single click and are routinely left on by accident. For each, the check
is not "is it on" but "was it a decision":

- **Mac and Vision Pro** — an app using the camera, location, or hand-offs to
  region-specific payment apps installed on a phone behaves badly on hardware where
  those apps do not exist. If the page says compatibility has not been verified, and
  nobody has tested it, recommend switching it off. A one-star review from a Mac user
  costs more than the install.
- **Volume purchase / education discount** — meaningful only for apps sold in bulk to
  schools and businesses. On a consumer app it is almost always an accident.

These are LOW severity. They are not review risks; they are quality and support risks.

## Common false positives

- **A high territory count is not itself a finding.** An app whose code has no
  regional coupling — a utility, a reader, a game — is fine everywhere. The finding
  requires *both* wide availability *and* single-market code.
- **Being single-market is not a problem.** It is a normal business choice. The
  problem is only ever the mismatch with the territory list.
- **"App Store software" tax category is the default** and correct for a free app
  selling physical goods outside the store. Not a finding.
- **A free app with no in-app purchases is correct** for physical-goods commerce —
  Apple's commission does not apply to physical goods, and no StoreKit integration is
  expected. Do not flag missing IAP.
- **Manual price tier absence is normal for free apps.** Nothing to check.

## Cannot be determined from this page

- **Which specific territories are selected.** The page shows a count and a link; the
  list is behind another click. Enough to flag the mismatch, not enough to name which
  to remove. Record this limit explicitly.
- Whether Mac or Vision Pro were actually tested — ask the user; there is no signal
  for it anywhere
- Whether pricing is competitive — commercial judgement, out of scope
- Pre-order configuration, unless visible in the screenshot
