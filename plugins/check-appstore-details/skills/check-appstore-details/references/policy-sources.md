# Policy sources

Apple's rules move, and a baked-in copy rots silently. Fetch these every run and
stamp the report with the date you fetched them.

Each entry below carries its **known failure mode**, established by testing rather
than assumed. Respect them — two of these sources cannot be read the obvious way.

## Fetch these

### 1. App Store Review Guidelines — the citations come from here
`https://developer.apple.com/app-store/review/guidelines/`

Renders real, quotable text. **Truncates mid-word partway through section 5.4**, and
the "last updated" date sits below section 5, inside the lost tail.

**Therefore: never ask for the whole document.** Ask a narrow, scoped question and
you get clean text well inside the truncation point. For example:

> Quote guideline 2.1 App Completeness and 2.3 Accurate Metadata verbatim.
> Quote guideline 5.1.1 sub-items (i) Privacy Policies and (ii) Permission verbatim.

Guidelines that matter most for this skill:

| Guideline | Covers |
|---|---|
| 2.1 App Completeness | demo accounts, working backend, functional URLs, no placeholders |
| 2.3 Accurate Metadata | description and screenshots matching the real app |
| 2.3.7 / 2.3.8 | keywords, app name and subtitle |
| 4.2 Minimum Functionality | an app that does too little, or does nothing in a shipped territory |
| 5.1.1 Data Collection | privacy policy link, permission purpose strings, data minimisation |
| 5.1.2 Data Use and Sharing | tracking, sharing with third parties |
| 5.1.5 Location Services | location permission proportionality |

### 2. Upcoming Requirements — deadlines and SDK floors
`https://developer.apple.com/news/upcoming-requirements/`

Renders fully and reliably. This is the authoritative source for "what is enforced
right now", and the reason this skill fetches at run time at all: it surfaces
requirements a model's training data will not contain.

Ask for every entry and its date. Items labelled "Since" are already in force.

Recurring items relevant here: the minimum Xcode and SDK version for uploads, the
privacy-manifest requirement for required-reason APIs, age-rating question updates,
and EU trader-status enforcement dates.

### 3. Apple Developer News — changes between guideline revisions
`https://developer.apple.com/news/`

Use when something looks like it changed recently, or when the user is asking about a
rejection that cites a rule you cannot find in the guidelines.

### 4. App Store Connect Help — for the UI-only flows
`https://developer.apple.com/help/app-store-connect/`

Use to give accurate navigation instructions, especially for the four screenshot-only
items. Sub-pages worth fetching on demand:

- `.../manage-compliance-information/manage-european-union-digital-services-act-trader-requirements/`
- the App Privacy and Pricing and Availability sections

## Do not use

**`https://developer.apple.com/documentation/appstoreconnectapi/*` — returns HTTP 404
to fetching.** The documentation site is a JavaScript application that fetch tools
cannot traverse. Both `.../appdatausages` and `.../app-data-usages` were confirmed
404. Do not cite it, and do not conclude an endpoint is absent because this 404'd.

If you ever need to establish what the App Store Connect API does or does not expose,
the machine-readable spec is the only reliable answer:

```
gh api "repos/EvanBacon/App-Store-Connect-OpenAPI-Spec/contents/specs/latest.json" \
   -H "Accept: application/vnd.github.raw" > /tmp/asc.json
```

This matters for one reason: it is how the "no API exists for this" claims in this
skill were established rather than guessed. Spec v4.4 (929 paths) contains **zero**
`appDataUsage` paths and **no** trader-status endpoint. Privacy labels, DSA trader
status and the Mac/Vision Pro availability toggles are genuinely absent from the
public API — not merely undocumented.

## Citing policy

A finding is presentable only with all three of:

- **guideline** — the number and title, e.g. `2.1 App Completeness`
- **quote** — a real fragment of the text you fetched, long enough to be a quotation
- **source** — the URL you fetched it from

`validate-findings.py` enforces this for any finding at stage `ready`. If you cannot
produce a quote, the finding is reported as "worth checking manually" and carries no
guideline reference at all. Never paraphrase a rule and present the paraphrase as
Apple's words.

## When a fetch fails

Say so explicitly, name the source, and downgrade every dependent finding to "check
manually". Do not fall back on remembered policy — that is exactly the failure this
file exists to prevent.
