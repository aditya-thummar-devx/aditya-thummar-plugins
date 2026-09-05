# Section recipes — building each section type

Load the recipe for the section you're on. Every section follows the same loop
(`interaction-protocol.md`); these are what's specific to each.

## Order to build in

Foundations first (they define vocabulary the rest reuses), prose-owner next, thin pieces last,
entry point last of all:
1. `reference/` specs the others cite (if any) · 2. `architecture/modules` (flow prose) ·
3. `architecture/<units>` (thin, link to modules) · 4. `dev/` · 5. `how-to/` · 6. `reference/reports`
+ `todo/` (moves) · 7. `README.md` (entry point — last, so its links resolve).
Adapt to the approved tree.

## how-to/ (non-technical)

For a non-technical operating surface only (CMS, admin, content editing). Voice: task-first, plain
words, no code identifiers in prose. Per item: *what it is · where it appears · what's safe to change
· danger notes*. Map machine names to friendly names once, in a table. Depth = purpose + safe fields,
not a schema dump.

## architecture/ (technical)

- **module/flow doc** (owns the prose): the end-to-end flow with `path:line` — entry, the units it
  spans, state/data, the API/services, and the real gotchas. Cross-link to auth/checkout/etc. rather
  than re-explaining them. This is where depth lives.
- **unit doc** (screen/route/endpoint — thin): what it renders/returns + which modules it uses +
  its own quirks, then a link into the module doc. Don't duplicate the flow.
- **index/router**: a table of units → the modules they touch, and which doc owns what.

## dev/

- **getting-started**: clone → install → run, from the real scripts (`package.json`/`Makefile`/…) —
  never invented commands.
- **setup/core-systems**: env/flavors, state, theming, i18n, hooks — moved from existing docs where
  they exist; each links to the canonical rule file for rules.
- **recipes/** (thin, links-only): "how do I add a <unit>/endpoint/…" — a short numbered flow that
  points at the canonical rule file section and any generator/skill. Never restates rules.
- **code-mirror/**: **structural** map — one index per source folder (folder-level by default), what
  each folder/notable file is *for*, linking to `architecture/` for behavior. No behavior prose, no
  props tables. Add it to the repo's code-index ignore file.

## reference/

- **live specs**: the maintained contract (event spec, API reference, security posture). Front-matter,
  no banner.
- **reports/**: move dated snapshots here with the not-maintained banner (`conventions.md`). Never
  edit their bodies — only add the banner + front-matter.
- **todo/**: living lists; `status: living`, no banner.
- Fix the inbound references of anything moved (skills/CI/README) in the same step.

## README.md (entry point)

Last. Audience router (who each section is for, with links), a one-line-per-section summary, the
"how these docs stay honest" note (front-matter + reports-never-edited), and where new docs go +
that the canonical rule file owns coding rules. Link straight to a section's index.
