# Page 05 — Version page, marketing assets

Screenshots, promotional text, description and keywords. This is where the listing
makes claims, and where those claims get checked against what the code can actually
do — guideline 2.3, the most common metadata rejection.

## What to ask for

> App Store Connect → your app → the version under **Prepare for Submission** →
> screenshot the Previews and Screenshots block, then the Promotional Text,
> Description and Keywords fields.

**Ask for description, promotional text and keywords as pasted text, not images.**
Those boxes scroll: a screenshot physically cannot contain a long description, and a
truncated read produces a wrong verdict. Say this when asking — the user does not
otherwise know why.

## Checks

| Check | Pass criteria |
|---|---|
| Every feature the description claims exists in the code | Each concrete claim traceable to real functionality |
| Promotional text claims exist in the code | Same test, shorter text |
| Screenshots exist for the required sizes | At least one size covering the declared device family |
| Screenshots show the real app | Not mockups, not marketing renders of nonexistent screens |
| iPad screenshots present if the app targets iPad | `TARGETED_DEVICE_FAMILY` includes `2` |
| No placeholder text anywhere | No "lorem", "TODO", "coming soon", "test" |
| Keywords do not waste characters | No duplicates, no words already covered by the name or category |

## How to verify

**Claims against code.** Take each concrete claim in the description and promotional
text and look for it in the repository — a screen, a navigation route, a translation
key, an API call. "Book an in-store appointment" should correspond to something
findable. Search the codebase directly; `findings.json` does not carry a feature index
detailed enough for this.

Cite **2.3 Accurate Metadata**, quoting it. Be precise about what you could not find,
and ask rather than assert: a feature may be behind a feature flag, or served from a
CMS, and absent from the code for good reason. A claim you cannot verify is a question,
not a finding.

**Device family and screenshot sizes.** `findings.json` reports
`TARGETED_DEVICE_FAMILY`. `1` is iPhone-only, so an empty iPad tab is correct and not
a finding. `1,2` means iPad screenshots are required and their absence blocks
submission. This is a cheap, definitive check — do it before anything subjective.

**Keywords.** A 100-character field. Flag, at LOW:

- the same word twice, including as part of a phrase ("fitness" and "home fitness"
  spend it twice)
- words duplicating the primary category, which Apple already indexes
- the app's own name, already indexed
- unused characters, with the count remaining

Keep this brief and mark it cosmetic. Deeper keyword strategy is ASO, which is out of
scope — offer the character arithmetic, not ranking advice.

**Placeholders.** 2.1 explicitly requires placeholder text to be scrubbed before
submission. Quote it if you find any.

## Common false positives

- **Fewer than the maximum screenshots is not a finding.** Apple requires one size,
  not ten images. Three good ones are fine.
- **One screenshot size is usually sufficient.** Apple scales a 6.5" set to larger
  displays. Suggest a native set for the newest size as an optional improvement, never
  as a requirement.
- **Marketing language is not a false claim.** "Luxury redefined" claims nothing
  testable. Only check concrete, functional claims — what the app *does*.
- **A feature absent from the code may still exist.** Server-driven UI, a CMS-supplied
  module, or a remote-config flag can all deliver a real feature the repository does
  not obviously contain. Ask.
- **An empty What's New is correct for a first release.** It only applies to updates.
- **Keywords under 100 characters are not a problem.** Unused space is an
  opportunity, not a defect. Do not inflate it.
- **A description in the primary language only is fine.** Additional localisations are
  optional.

## Cannot be determined from this page

- Whether screenshots depict the *current* build — they may be from an older version,
  and there is no way to tell from the image
- Whether screenshot text is correctly localised for each storefront
- Keyword ranking or search volume — ASO, out of scope
- Whether a claim is delivered by a server rather than the binary, without asking
- App previews (video), unless the user sends them separately
