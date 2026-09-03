# check-appstore-details

A Claude Code plugin that audits an iOS app's **App Store listing against its own
codebase** before you submit, then walks you through fixing each problem one page at a
time — verifying every fix before it moves on.

> Not affiliated with, endorsed by, or connected to Apple Inc. "App Store" and "App
> Store Connect" are trademarks of Apple Inc., used here only to describe what the tool
> works with.

## Why

A submission has to keep two things in agreement: what the listing *claims*, and what
the code actually *does*. Nothing checks those against each other. Metadata linters
read the listing in isolation; nothing reads your `Info.plist`, `PrivacyInfo.xcprivacy`,
`project.pbxproj` and dependency manifest and compares them to what you declared on the
store.

That is exactly where the worst rejections hide — a privacy manifest that contradicts
your privacy labels, a permission you declare but never use, an SMS-login demo account
a reviewer can never sign into, an app shipped to 175 countries whose checkout only
works in one.

## What it does

- **Fetches current Apple policy at run time** — the Review Guidelines and Upcoming
  Requirements — so findings cite live rules, not a model's stale memory.
- **Reads your project** deterministically: version numbers across every target,
  declared-vs-used permissions, the privacy manifest, tracking SDKs, region signals,
  and how the app's login works.
- **Collects the listing from you** as screenshots or pasted text. No App Store Connect
  credentials, ever.
- **Fixes as it goes.** Instead of a report at the end, it takes one listing page at a
  time: tells you what's wrong, quotes the guideline, gives you the exact fix, waits for
  you to make it, then re-checks.

## What it deliberately does not do

- **No App Store Connect API, no `.p8` key, no credentials.** It cannot change your
  listing — every store-side edit is yours to make.
- **No approval prediction.** It says "likely flagged", never "will pass".
- **No Google Play.** App Store only.
- **No invented rules.** Every presented finding carries a real quotation from the
  policy it fetched; anything it cannot cite is downgraded to "check this manually".

Four things — privacy labels, DSA trader status, Mac/Vision Pro availability, and
volume-purchase pricing — have no App Store Connect API at all (verified against
Apple's OpenAPI spec). Those are collected by screenshot, always.

## Install

Local development:

```
claude --plugin-dir /path/to/check-appstore-details
```

Or via a marketplace, once published:

```
/plugin marketplace add <owner>/check-appstore-details
/plugin install check-appstore-details
```

## Use

From inside any iOS project:

```
/check-appstore-details
```

or just ask — "check my app store details", "am I ready to submit", "will Apple reject
this".

It prints what it read (branch, commit, framework, findings), tells you which listing
pages it needs, and then works through them with you.

## What it supports

Detectors are written generically. **React Native and Expo are verified.** Flutter,
native iOS and Capacitor are detected but not yet fully verified — the shared checks
still apply, and the tool says so rather than implying full coverage.

## How it's built

```
skills/check-appstore-details/
├── SKILL.md              the run flow, hard rules, and per-page loop
├── scripts/
│   ├── scan-project.py       deterministic code read → findings.json
│   ├── validate-findings.py  blocking evidence validator (has --self-test)
│   ├── check-urls.py         reachability check for the listing's public URLs
│   └── signals.json          detection tables (payment SDKs, currencies, …)
└── references/
    ├── policy-sources.md     what to fetch, and each source's known quirks
    ├── page-01..08.md        one file per App Store Connect page
    ├── code-checks.md        the code-side reasoning
    ├── signal-tables.md      how the detection tables work
    └── fix-templates.md      drafted review notes and edits
```

The scanner does only what is deterministic; the skill does the judgement. Every code
finding must cite a file, a real line, and matching text, or the validator refuses to
let it be presented — the guard against inventing a problem that isn't there.

## Licence

MIT. See [LICENSE](LICENSE).
