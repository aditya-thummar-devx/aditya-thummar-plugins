# Page 01 — App Information (top)

Establishes identity: that the listing you are auditing is the app in this repository,
and that its name, category and content declarations are defensible. Cheap page, but
it must come first — everything afterwards assumes the right app.

## What to ask for

> App Store Connect → your app → **App Information**. Screenshot the top section,
> down to and including Content Rights.

Screenshot is fine here; every field is short and on screen. Ask for the **name and
subtitle as text** if either looks truncated in the image.

## Checks

| Check | Pass criteria |
|---|---|
| Bundle ID matches the repository | Listing bundle ID equals `PRODUCT_BUNDLE_IDENTIFIER` for the app target in `findings.json` |
| Name is present and not a placeholder | No "test", "demo", "untitled", no trailing version numbers |
| Subtitle, if set, does not repeat the name | Wasted characters otherwise; empty is acceptable |
| Primary category fits what the app does | Compare against the feature evidence in `findings.json` |
| Content rights declaration is consistent | If the app displays third-party content, the declaration must say so |
| Primary language matches the app's actual copy | An app whose strings are all in one language should not declare another |

## How to verify

**Bundle ID** is the one hard identity check. If it does not match the app target in
`findings.json`, stop the whole audit — you are looking at a different app's listing,
and every subsequent comparison would be meaningless. Ask which is correct.

Note the app target specifically: extensions carry a bundle ID beneath the app's
(`com.example.app.NotificationService`), and the listing always shows the app's.

**Category** against reality. A shopping app in Utilities, or a game in Business,
draws a rejection under 2.3 Accurate Metadata. Cite 2.3 with a quote if you flag it.

**Content rights.** "This app does not contain, show, or access third-party content"
is wrong if the app renders a CMS feed, user reviews, embedded video, or a web view of
someone else's site. Check `findings.json` for a web-view dependency or a CMS client
before accepting the declaration.

**Name and subtitle** fall under 2.3.7. Keyword stuffing in either is a rejection.

## Common false positives

- **A bundle ID appearing more than once in `findings.json` is normal.** Debug,
  Release and a UAT flavour commonly share one bundle ID across six configuration
  records. Different bundle IDs across app configurations are the unusual case worth
  a question.
- **An empty subtitle is not a finding.** It is optional. Mention it once as an
  opportunity and move on; it is not a review risk.
- **A localised name differing from the display name is not a mismatch.** The listing
  name and `INFOPLIST_KEY_CFBundleDisplayName` serve different purposes and routinely
  differ in punctuation, spacing or accents.
- **Declaring third-party content is not a problem to fix.** It only needs to be
  *accurate*. Over-declaring costs nothing.

## Cannot be determined from this page

- Whether the name infringes a trademark — legal judgement, outside this skill
- Whether the category is optimal for discovery — that is ASO, explicitly out of scope
- Age-rating answers, encryption and trader status — page 02
- Whether the app is available anywhere at all — page 03
