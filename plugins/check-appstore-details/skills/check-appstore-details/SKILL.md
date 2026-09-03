---
name: check-appstore-details
description: Audit an iOS app's App Store listing against its own codebase before submission, then walk the user through fixing each problem. Fetches current Apple policy at run time, reads the project's version numbers, permissions, privacy manifest and tracking SDKs, collects listing details from user-supplied screenshots or pasted text, and verifies each fix before moving on. Needs no App Store Connect credentials. Use when the user says "check my app store details", "am I ready to submit", "will Apple reject this", "app review", "pre-submission check", or asks why a submission was rejected. Do NOT use for Google Play listings, for App Store Optimization or keyword-ranking advice, or for writing marketing copy.
version: 0.1.0
trigger: /check-appstore-details
allowed-tools: [Read, Edit, Glob, Grep, Bash, WebFetch, AskUserQuestion]
---

# check-appstore-details

Compares what an App Store listing claims against what the code actually does, then
fixes the gaps one page at a time. Portable: this directory can be copied into any
repository's `.claude/skills/` and run without edits.

- Needs **no App Store Connect credentials**. Listing data comes from the user, as
  screenshots or pasted text.
- The tool **cannot change a listing**. It has no write path. Every store-side edit
  is made by the user.
- Code fixes are applied **one at a time, on explicit approval**, then re-read.

## Hard rules

1. **Never assert a policy requirement without a citation.** Every finding you
   present carries a guideline number *and* a quoted fragment from the policy fetched
   in this run. No quote means you say "check this manually" — never state it as
   fact. Inventing a plausible-sounding Apple rule is the worst failure available
   here, because it sends the user to change something that was already correct.
2. **Never ask for anything you can read from the repository.** "Which framework is
   this?" is a failure — run the scanner. Screenshots are requested only for the four
   things Apple exposes nowhere. The known failure mode of question-driven skills is
   asking lazy questions instead of doing the work.
3. **Never score a field you cannot read.** If a requested field is cropped, scrolled
   out of frame or illegible, say which field is missing and ask again. A false
   "verified" is worse than no check at all.
4. **Quote the value you read.** When checking a screenshot, restate the exact value
   observed before judging it. A finding that cannot quote what it saw does not stand.
5. **Verified, attested and pending are three different results.** "The test number
   receives its code" is *attested* by the user and unverifiable by any tool. Apple's
   trader verification is *pending*. Never show either as verified.
6. **Never echo a credential.** Demo-account passwords appear in listing screenshots.
   Confirm one is present; never repeat it back in output.
7. **Never batch code edits.** One finding, one diff, one approval, then re-read the
   file to confirm. If the user declines, record it as skipped and move on.
8. **Never suggest a store-side automation.** Give the navigation path and let the
   user act.
9. **Report what you actually read.** Every run states branch, commit and whether the
   tree is dirty. A finding derived from a stale tree is a wrong finding — this has
   happened in practice, mid-session, when a branch changed underneath an audit.
10. **Never predict approval.** "Likely flagged", never "will pass". Human reviewers
    do things no tool anticipates.
11. **Never work around the validator.** If `validate-findings.py` rejects a finding,
    fix the citation or drop the finding. Do not weaken the evidence to get past it.

## Run flow

### Step 1 — Fetch today's policy

Load `references/policy-sources.md` and fetch the sources it lists. Read them with
**narrow, question-scoped prompts** — the Review Guidelines page truncates partway
through section 5, so asking for the whole document loses the tail.

Report a dated header before anything else:

> Policy as of `<date>`, fetched from developer.apple.com.
> Currently enforced and relevant here: `<items>`

If a fetch fails, say so and continue — but every finding that depended on it becomes
"check manually", per hard rule 1.

### Step 2 — Read the project

```
python3 scripts/scan-project.py --path <project-root>
python3 scripts/validate-findings.py
```

The scanner writes `.check-appstore-details/findings.json` and adds that directory to
`.git/info/exclude`, so it never dirties the target repo. Read the JSON. Do not
re-derive by hand what the scanner already produced.

If the validator exits non-zero, **stop**. Findings are unusable until it passes.

`notChecked` entries are as important as findings: they are the checks that cannot be
settled from a repository, and they drive Step 4.

### Step 3 — Show the detection table, then the plan

Present what was detected **before asking for anything**, so a wrong reading is
corrected now rather than after eight screenshots:

> Read `<branch>` @ `<commit>`, working tree `<clean|dirty>`
> Framework, targets, bundle id, device family, tracking SDKs, login type
> Findings from code: `<n>` · Needs your input: `<m>`

Then list the checks you will run, and say plainly which listing pages you need and
which you can do nothing about without them. End with one `AskUserQuestion` to
proceed. Nothing is collected until the user approves.

### Step 4 — Collect and fix, one page at a time

Work through the pages in order, loading **one reference file at a time**:

- `references/page-01-app-information.md`
- `references/page-02-compliance.md`
- `references/page-03-pricing-availability.md`
- `references/page-04-app-privacy.md`
- `references/page-05-version-marketing.md`
- `references/page-06-version-urls.md`
- `references/page-07-version-review.md`
- `references/page-08-builds.md`

Each file states what to ask for, what to compare it against, the guideline to cite,
and its own **Common false positives** — test every candidate against that list before
it becomes a finding. Move anything in its **Cannot be determined from this page**
list into the not-checked list with a reason.

For long text fields ask for **pasted text, not a screenshot**: App Store Connect's
text boxes scroll, so an image physically cannot contain the whole description.

### Step 5 — The loop, per page

1. Ask for the page. Give the exact navigation path.
2. Read it and **immediately condense it to a few lines of text**. Reason from that
   text afterwards, not from the image — this is what keeps a long session inside the
   context window.
3. Compare against `findings.json` and today's policy.
4. Clean checks get **one line each**. No ceremony.
5. For each problem: what is wrong, the guideline with its quote, where to fix it, and
   drafted replacement text where `references/fix-templates.md` has one.
6. Group every problem on that page into **one round of fixes**. Never send the user
   to the same page twice.
7. Close with one `AskUserQuestion`: *fixed it* / *skip this* / *show me what's left*.
   - **fixed it** → ask for a fresh screenshot of that page only, re-verify, report
     per item. If a value is unchanged, ask whether it was deliberate rather than
     asserting failure.
   - **skip this** → record as skipped with the reason. Do not re-raise it.
   - **show me what's left** → print the remaining queue, then return here.

### Step 6 — Code fixes

Load `references/code-checks.md` and `references/fix-templates.md`. For each code
finding: show the file, the line, the exact diff, and the guideline. One approval per
fix. After applying, re-read the file and confirm. Re-run the scanner and validator
once at the end.

### Step 7 — Re-evaluate the cascade

Findings depend on each other. Narrowing territories can retire an EU-specific
obligation outright. After each fix, re-check anything downstream and say so out
loud — never ask the user to fix something that stopped being a problem two steps ago.

### Step 8 — Close with a tally, not a report

```
Done. <n> checks needed attention.
  verified fixed      <n>
  attested by you     <n>   (what, and why no tool can confirm it)
  pending Apple       <n>   (what you are waiting on)
  pending your build  <n>
  skipped             <n>

Before you hit Submit:
  · <the one or two things still open>
```

No document. Everything was resolved as you went.

## What this skill cannot do

- **Privacy labels, DSA trader status, Mac and Vision Pro availability, and volume
  purchase have no API and are not in the repository.** They are screenshot-only,
  permanently, and their accuracy rests on what the user sends.
- **The territory list is a count, not a list.** Enough to flag "shipped to 175, code
  supports one market"; not enough to name which to drop.
- **Build history is partial.** Only what is on screen.
- **Whether a demo login actually works is unverifiable.** No tool can send an SMS or
  reach a backend. It ends attested, never verified.
- **Frameworks other than React Native and Expo are detected but unverified** in this
  version. Shared checks still apply; say so rather than implying full coverage.

A largely not-checked page is an honest result. Do not pad it with findings dressed
up as outcomes.

## Before you present anything

- [ ] Policy was fetched this run, and the report carries its date
- [ ] `scan-project.py` ran; `validate-findings.py` exited zero
- [ ] Branch, commit and dirty state were stated to the user
- [ ] The detection table was shown before any screenshot was requested
- [ ] Every finding cites a guideline number and a real quotation
- [ ] No finding rests on a field that was not legible
- [ ] Every screenshot-derived judgement quotes the value it read
- [ ] Attested and pending items are not labelled verified
- [ ] No demo-account password appears anywhere in the output
- [ ] Nothing in the target repo was edited except approved fixes
