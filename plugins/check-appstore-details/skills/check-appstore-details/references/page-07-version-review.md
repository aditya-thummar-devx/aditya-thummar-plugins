# Page 07 — Version page, App Review Information

The page that decides whether a reviewer can use the app at all. If they cannot sign
in, nothing else on the listing matters — guideline 2.1 rejects it regardless of how
good the rest is.

## What to ask for

> Same version page, bottom. Screenshot the Build section, App Review Information
> (contact details, sign-in information) and App Store Version Release.

Ask for the **review notes as pasted text** — the notes box scrolls and holds up to
4,000 characters. **Do not ask for the demo password to be typed out**; the screenshot
is enough to confirm one is present, and hard rule 6 forbids echoing it.

## Checks

| Check | Pass criteria |
|---|---|
| A build is attached | Nothing can be submitted without one |
| Sign-in required is set correctly | Matches whether the app actually has a login |
| Demo credentials present when a login exists | Both fields filled |
| The demo credentials are **usable by a reviewer** | Reviewer can complete sign-in unaided |
| Review notes explain the login | Especially any non-obvious arrangement |
| Review notes explain regional limits | If the app only works in some territories |
| Contact details are a real, reachable person | Not a shared alias nobody reads |
| Release option is deliberate | Manual or automatic, chosen not defaulted |

## How to verify

**The login wall is the critical check.** `findings.json` reports the login type. Take
each case on its own terms:

- **`otpSms`** — the reviewer cannot receive an SMS. Unless the demo number bypasses
  SMS on the backend and returns a fixed code, the reviewer is stuck at the login
  screen. This is a BLOCKER, and it is the single most likely reason a submission with
  an otherwise clean listing gets rejected.

  Guideline 2.1 is unusually explicit here — quote the part about including demo
  account info *and turning on your backend service*. Also quote the alternative it
  offers: where legal or security obligations prevent a demo account, a **built-in
  demo mode** is permitted with prior approval from Apple, and it must exhibit the
  app's full features.

  No tool can verify this. Ask the user directly whether the test number and code work
  end to end, and record the answer as **attested**, never verified. If they have not
  tested it, say plainly that this is the highest-risk item in the whole audit.

- **`social`** — the reviewer needs a working account with that provider. Confirm the
  demo credentials work for the provider, not just for your backend.

- **`biometric`** — confirm there is a passcode or password fallback. A reviewer on a
  simulator or a fresh device may have no enrolled biometrics.

- **no login detected** — "Sign-in required" should be off. If it is on with no login
  in the code, ask which is stale.

**Review notes.** An empty notes field is a real finding whenever anything about the
app is non-obvious. At minimum it should cover:

1. how to sign in, including the demo credentials and any bypass arrangement
2. any regional limitation — which country to use for an address, which payment method
   a reviewer will encounter, and what to expect at checkout
3. anything a reviewer would otherwise read as broken

`references/fix-templates.md` has drafted text for each. Offer it filled in from what
you already know, and let the user edit.

**Regional limits.** If page 03 produced a territory finding, the notes must explain
how to test. A reviewer outside the supported market hitting a dead checkout with no
explanation rejects the build.

**Release option.** Manual release is the safer default for a first submission — the
user chooses when it goes live. Automatic is fine but should be a decision. LOW either
way; just confirm it was chosen.

## Common false positives

- **A fake-looking demo phone number is not automatically wrong.** Backends commonly
  whitelist a test number with a fixed code. The finding is not "this number looks
  fake" — it is "confirm this actually works". Ask; do not assume either way.
- **Sign-in required with a partial login is legitimate.** Many apps allow browsing
  anonymously and only require an account at checkout. That still counts as having a
  login, and still needs working credentials.
- **A shared support alias in the contact field is acceptable** if it is genuinely
  monitored. Ask rather than flagging.
- **Empty notes are fine for a genuinely simple app** with no login, one market, and
  no unusual flows. Do not manufacture a finding to fill the field.
- **A build in "Processing" is not a missing build.** Processing takes up to about
  half an hour. Record it as pending rather than as a finding.
- **The notes do not need to repeat the description.** They exist for the reviewer's
  practical problems, not to market the app.

## Cannot be determined from this page

- **Whether the demo credentials actually work.** Unverifiable by any tool — it needs
  a live SMS or a backend check. Always ends attested.
- Whether the contact person will respond within Apple's window
- Whether an attachment was uploaded, unless visible in the screenshot
- Full build history — page 08
- Whether a previous submission was rejected, and why — ask the user; a past rejection
  reason is the most useful context available and is worth asking for explicitly
