# Page 06 — Version page, URLs and version string

Short page, two hard checks. The version string here must agree with the build, and
the URLs must actually resolve — 2.1 requires "fully functional URLs".

## What to ask for

> Same version page, scrolled down. Screenshot Support URL, Marketing URL, Version and
> Copyright.

Ask for the **URLs as text** so they can be tested without transcription error.

## Checks

| Check | Pass criteria |
|---|---|
| Version string matches the code | Equals `MARKETING_VERSION` for the app target |
| Support URL is present and reachable | Required field; must return a real page |
| Marketing URL, if set, is reachable | Optional field, but a dead link is worse than none |
| Copyright names the right legal entity | Matches the entity that owns the app |
| No placeholder URLs | No localhost, no staging host, no "example.com" |

## How to verify

**Version string.** `findings.json` reports `MARKETING_VERSION` per target. Compare
directly. This is the check that catches the classic `1.0` versus `1.0.0` mismatch —
those are different strings, and App Store Connect treats them as such.

There are up to four values that must agree:

1. this listing field
2. `MARKETING_VERSION` on the app target
3. `MARKETING_VERSION` on every extension (a mismatch here fails upload validation
   before review — already a BLOCKER in `findings.json`)
4. Android's `versionName`, if the project ships both

State which direction to fix. If a build carrying the code's version has **already
been uploaded**, that version is frozen in the binary — so the listing field is the
one to change. If no build is uploaded yet, either side can move, and aligning in code
is usually cleaner because it fixes the extensions at the same time.

**URLs.** Run the checker:

```
python3 scripts/check-urls.py <support-url> <marketing-url> <privacy-policy-url>
```

Quote 2.1 on functional URLs if one fails. Treat the result carefully — see false
positives below.

**Copyright.** Cross-check against the DSA trader question on page 02. A registered
company named here alongside a "non-trader" declaration there is a contradiction
visible on one listing, and it is worth pointing at both at once.

Also sanity-check the year and that the entity is a real legal name rather than a
product name.

## Common false positives

- **A 403 does not mean the page is dead.** Many hosts and CDNs block non-browser user
  agents. Report the status code and ask the user to confirm in a browser rather than
  declaring the URL broken.
- **A redirect chain is fine** if it ends at 200. Only flag a chain that loops or ends
  in an error.
- **An empty Marketing URL is correct.** It is optional and its absence is not a
  finding. Only a *broken* one matters.
- **`1.0` versus `1.0.0` may already be resolved in the code.** Read the current value
  from `findings.json` rather than from an earlier turn in the conversation — the
  working tree may have moved. This has happened mid-audit.
- **A support URL pointing at a contact form rather than a help centre is acceptable.**
  Apple requires a way to reach support, not a documentation site.
- **A copyright year one behind the current year is not a finding.** It refers to the
  work, not to today.

## Cannot be determined from this page

- Whether the support page is actually monitored by a human
- Whether the named entity is the correct legal owner — ask, do not infer
- Which build is attached to this version — page 07
- Whether the version has already been used for a previous release
