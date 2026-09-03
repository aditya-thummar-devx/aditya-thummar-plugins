# Signal tables

The machine-readable tables live in **`scripts/signals.json`**. That file is the
single source of truth; this file explains the method so the two cannot drift apart.
Do not restate table contents here.

## What the tables are for

The scanner cannot know what an app *is*. It infers from what the code carries:

| Table | Infers |
|---|---|
| `trackingSdks` | whether a "no tracking" declaration is credible |
| `paymentSdks`, `paymentUrlSchemes` | which market the app can actually transact in |
| `currencies`, `postalValidators` | whether the code is pinned to one country |
| `loginKinds` | whether a reviewer can get past the login wall |
| `permissionUsage` | whether each declared permission is actually exercised |

## The adequacy test

**Removing any one entry must not change behaviour for one specific app only.**

If deleting `razorpay` stopped the region check working for exactly one project, the
table is too narrow and has become a hard-coded description of that project. The fix
is always to broaden — add the other twenty-nine payment SDKs — never to special-case.

The same test applies to currencies, postal formats and login providers. A table with
one region's entries is not a signal table, it is a hidden assumption.

## The strong/weak split, and why it exists

`permissionUsage` splits each key into `strong` and `weak` needles, and the two
directions of the permission audit use them **asymmetrically**:

| Direction | Needles used | Why |
|---|---|---|
| declared but unused | strong **and** weak | a hit *suppresses* a finding, so being permissive is conservative; a false hit costs only a missed low-severity report |
| used but undeclared | **strong only** | a hit *creates* a BLOCKER; a false positive at that severity is far more damaging than a miss |

This is not theoretical. A bare `startScan` needle, matched as a substring, hit a
QR-code handler named `startScanFromSheet` and produced two BLOCKER Bluetooth findings
against an app containing no Bluetooth code at all. Two fixes came out of it, both now
in the scanner:

- **Identifier-shaped needles match on word boundaries**, not as substrings, so
  `startScan` no longer matches `startScanFromSheet`. Package names and dotted calls
  still match as substrings, since word boundaries behave badly around `/` and `-`.
- **The undeclared direction only trusts strong needles** — package names and
  distinctive platform APIs that mean one thing.

## Most-specific-match-wins

A dependency is reported under the **longest** matching candidate. Without this, a
project depending only on `react-native-fbsdk-next` reports both that and
`react-native-fbsdk`, because the shorter name is a prefix of the longer one. Two
entries for one dependency reads as two SDKs and inflates the finding.

## Currency detection needs context

A bare three-letter match is far too loose. `SAR` appears in `Hong Kong SAR China`
inside any country-picker list, and a naive match reports the Saudi riyal in an app
that has never seen one — which then breaks the "single currency" inference.

A currency code counts only when it is a **quoted token** (`'INR'`, `"USD"`) or sits
on a line that is otherwise talking about money (`currenc|price|amount|money|payment|
total|symbol|locale`).

## Adding to the tables

1. Add to `scripts/signals.json`, never inline in the scanner.
2. For `permissionUsage`, decide strong versus weak deliberately: could this string
   plausibly mean something else in an unrelated codebase? If yes, it is weak.
3. Prefer package names over API symbols — a package name in a dependency list is
   unambiguous in a way an identifier never is.
4. Add entries for regions the tables do not yet cover before adding a second entry
   for one already covered.
