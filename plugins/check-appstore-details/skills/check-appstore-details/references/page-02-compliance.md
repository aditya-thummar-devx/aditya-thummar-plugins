# Page 02 — Compliance and regulatory

Age ratings, encryption, and the regulatory declarations. Two items here can remove an
app from a storefront after it has already shipped, which makes them worth more
attention than their obscurity suggests.

**Run this page after page 03.** Territory scope decides whether half of it applies.

## What to ask for

> App Store Connect → your app → **App Information**, scrolled down. Screenshot from
> Age Ratings through App Store Regulations & Permits.

## Checks

| Check | Pass criteria |
|---|---|
| Age rating matches actual content | No rating-relevant content the questionnaire denies |
| Age-rating questions answered under the current system | Apple replaced the questionnaire; unanswered apps get blocked at submission |
| Encryption declaration consistent with the plist | Listing state agrees with `ITSAppUsesNonExemptEncryption` |
| DSA trader status declared, and **correct** | A company selling goods or services is a trader |
| Trader details verified, if trader and shipping to the EU | Unverified means EU removal |
| Other permits are genuinely not applicable | China ICP, Vietnam game licence, regulated medical device |

## How to verify

**Encryption.** `findings.json` reports `usesNonExemptEncryption` from `Info.plist`.
`false` declares the exempt case — standard HTTPS and platform crypto only — and if
that key is present, App Store Connect stops asking at submission and no document
upload is needed. If the page still shows an encryption prompt while the plist says
`false`, that is normal and not a finding. Flag only the reverse: a missing plist key,
or a plist saying `true` with nothing declared.

**DSA trader status** is the one to get right. Under the Digital Services Act, Apple
must publish verified trader contact details for traders distributing in the EU.

- A **registered company** selling physical goods, digital goods or services **is a
  trader.** Cross-check the Copyright field on page 06 — a company name there and
  "non-trader" here is a contradiction on the same listing.
- Traders must submit and have **verified** an address, phone number and email, which
  then appear publicly on the product page. Verification takes days, so it ends
  **pending Apple**, never verified in-session.
- Enforcement is real: apps without verified trader status are removed from the EU
  App Store, and trader status is required to submit updates for EU-distributed apps.
  Fetch the exact dates from Upcoming Requirements rather than quoting from memory.
- **Narrowing territories out of the EU removes the obligation entirely.** If page 03
  produced a territory finding, resolve it first — this item may disappear.

**Age ratings.** Compare the summary against what the app actually contains. A
shopping app rated 4+ is unremarkable. Look for contradictions: user-generated
content, unrestricted web access, or in-app chat that the questionnaire denies. A web
view pointed at arbitrary URLs is unrestricted web access.

**China ICP** applies only if mainland China is in the territory list. **Vietnam game
licence** only for games. **Regulated medical device** only for Medical or Health &
Fitness apps, or where the questionnaire declared frequent medical information.

## Common false positives

- **An encryption upload prompt is not an outstanding task** when the plist already
  declares `ITSAppUsesNonExemptEncryption = false`. The page shows the prompt
  regardless; the plist key is what settles it at submission.
- **"Non-trader" is not automatically wrong.** An individual developer publishing a
  free app with no commercial activity is genuinely a non-trader. It is wrong when a
  registered company transacts. Decide on the entity and the commerce, not on vibes.
- **A blank China ICP field is correct for most apps.** Only a finding if mainland
  China is in the territory list.
- **Regional age-rating variations are normal.** Different ratings for Brazil, Korea
  and Vietnam alongside a global rating is Apple's own mechanism, not a
  misconfiguration.
- **A 4+ rating with a login wall is not a contradiction.** Age rating is about
  content, not about account requirements.

## Cannot be determined from this page

- **Whether trader verification has been approved** — Apple-side, takes days, and the
  page shows only what was submitted
- Whether the entity named is the correct legal entity — ask the user, do not infer
- Whether age-rating answers are individually correct — the questionnaire spans
  several pages; this page shows the resulting summary only
- Whether the app is actually distributed in the EU — page 03
