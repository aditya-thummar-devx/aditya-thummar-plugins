---
name: update-docs
description: Analyze any project and build, restructure, or gap-fill its documentation as an audience-split tree written from the code — proposing the tree first and then working one approval-gated section at a time. Detects the stack (mobile / web / backend / library / CLI / monorepo) and adapts the tree and vocabulary to it. Stamps every doc with source/verified_at/verified_commit front-matter, links to the canonical rule file instead of restating it, moves existing docs with git mv while fixing inbound references, and verifies every section for broken links before handing it back. Use when the user says "document this project", "update/rebuild the docs", "build a docs tree", "what's undocumented", "restructure the docs", or "onboard docs". Do NOT use to write a single one-off file (just write it), or for API-reference generation from doc comments (that's a generator's job).
version: 0.1.0
trigger: /update-docs
allowed-tools: [Read, Write, Edit, Glob, Grep, Bash, Agent, AskUserQuestion]
---

# update-docs

Turns a codebase into a documentation tree organized **by audience**, written **from the code**,
and built **one section at a time with the user in control**. Portable: this directory can be
copied into any repository's `.claude/skills/` and run without edits.

Three situations, one flow — the run detects which applies and adapts:
- **Greenfield** — little or no docs. Propose a tree, build it.
- **Restructure** — docs exist but are messy/flat. Move them into the tree (`git mv`), fix inbound
  references, fill gaps.
- **Gap-fill** — a real tree exists. Audit code vs docs and add only what's missing.

The references in `references/` carry the detail; load **one at a time**, at the step that needs it.
Do not preload them.

## Hard rules

1. **Write from the code, with evidence.** Every doc's claims trace to real files (cite
   `path:line` while drafting). Never invent a flow, a screen, or an endpoint that isn't in the
   tree. Inventing plausible-sounding behavior is the worst failure here — it sends readers to rely
   on something that doesn't exist.
2. **Never ask for what the repo can answer.** Run `scan_project.py`; read code with subagents.
   "What framework is this?" is a failure — the scan already said. Ask the user only for intent
   (which sections matter, how deep) and for things genuinely outside the repo (screenshots, access).
3. **Front-matter on every doc** — `source` (the code it mirrors), `verified_at`, `verified_commit`.
   Currency becomes checkable. See `references/conventions.md`.
4. **`reports/` are snapshots, never edited.** Dated point-in-time material (audits, migrations,
   feasibility) is written once and cited as evidence, never updated. Living lists go in `todo/`.
5. **Link, don't restate.** Coding rules live in the repo's canonical file (`CLAUDE.md` / `AGENTS.md`
   / `CONTRIBUTING.md` / `README`). Docs link to it; a rule appearing in both places is a bug.
6. **Moves preserve history and fix references in the same step.** Relocate with `git mv`. Every
   inbound reference to a moved path — in code comments, CI files, other skills, `README`s — is
   repointed in the same step, or tooling breaks silently later.
7. **One section at a time; stop before and after.** Preview a section and wait for approval before
   building it; hand it back and wait for the user to verify before the next. Never chain sections.
8. **Verify before handing back.** Run `check_docs.py` on the section; never claim a section is done
   on unverified links. A broken cross-link is the quiet failure a docs tree dies of.
9. **State branch / commit / dirty every run.** Docs derived from a stale or dirty tree are wrong;
   say what you read.
10. **Adapt vocabulary to the stack.** Say "screens" for a mobile app, "routes/pages" for web,
    "endpoints/services" for a backend, "public API" for a library. Don't force one project's words
    on another.

## Run flow

### Step 1 — Read the project
```
python3 scripts/scan_project.py --path <project-root>
```
Reads `.update-docs/structure.json` (kind, frameworks, top-level source dirs, candidate
screens/routes/endpoints/modules, convention files, and an inventory of **every** existing doc with
its front-matter state). It writes only to `.update-docs/` and adds that to `.git/info/exclude`, so
the target repo stays clean. **Read the JSON — do not re-derive the layout by hand.** Then state
branch/commit/dirty to the user. If the tree is dirty, note it.

### Step 2 — Decide the mode
From `existingDocs` in the scan: none/trivial → **greenfield**; many flat/loose docs or a `docs/`
without a clear tree → **restructure**; a real audience tree already present → **gap-fill**. Load
`references/detection.md` to map the scan onto a stack kind and its vocabulary.

### Step 3 — Propose the tree, then stop
Load `references/audience-tree.md`. Adapt the audience skeleton (how-to · architecture · dev ·
reference) to the detected kind, and — for restructure/gap-fill — to the docs that already exist.
Present:
- the **proposed tree** (folders + a one-line purpose each), who each top section is for,
- for restructure: a **move map** (existing doc → new home) so nothing is orphaned,
- the **granularity choices** that matter (e.g. per-folder vs per-file code mirror; which flows get
  their own doc), each with a recommendation.

Use `AskUserQuestion` for the real forks. **Do not write anything yet.** Iterate until the user
approves the final tree. This is the single most important checkpoint — a wrong tree wastes every
section after it.

### Step 4 — Build, one main folder at a time
Load `references/section-recipes.md` for the section type, and follow `references/interaction-protocol.md`
for the loop. For each top-level section, in the order the user approved:

1. **Preview** — name the section, list the docs it will contain, the **sources** each will read,
   and split *auto-derived from code* vs *needs you*. **Stop for approval.**
2. **Build** — explore the relevant code (subagents for breadth), then write the docs **from code**:
   front-matter, per-topic folders, cross-links to sibling docs and to the canonical rule file. For
   restructure: `git mv` the existing doc into place and fix its inbound references. For a code
   mirror or spec, stay structural and link to the flow docs rather than duplicating them.
3. **Verify** — `python3 scripts/check_docs.py <docs-dir>` (add `--stale-path <old-dir>` during a
   restructure to catch links back into the old location). Fix everything it flags. Report the
   result.
4. **Hand back** — ask the user to review this section and confirm before you continue. **Stop.**

Repeat for the next section.

### Step 5 — Close
Run `check_docs.py` over the whole tree. Give a coverage summary: sections built, docs written/moved,
and any **known-thin docs or remaining gaps** stated honestly (a gap named is better than a gap
hidden). If a top-level entry point (`README`/index) is part of the approved tree, write it last so
its links resolve.

## What this skill cannot do
- **Invent domain knowledge that isn't in the code.** If behavior lives only in a person's head or a
  backend you can't read, say so and leave a marked `TODO`, don't guess.
- **Guarantee completeness.** It documents what the code shows; it names what it couldn't reach.
- **Write great prose about a stack it misread.** If detection looks wrong, surface it in Step 1 and
  let the user correct it before proposing a tree.
- **Touch secrets.** Never copy tokens, keys, or `.env` values into a doc.

## Before you present anything
- [ ] `scan_project.py` ran; you read `structure.json` rather than re-deriving the layout
- [ ] Branch, commit and dirty state were stated to the user
- [ ] The tree was approved before any doc was written; a move map was shown for a restructure
- [ ] Every doc written carries `source` / `verified_at` / `verified_commit`
- [ ] Each section was verified with `check_docs.py` before hand-back; nothing links into a removed dir
- [ ] Moved docs used `git mv` and every inbound reference was repointed in the same step
- [ ] Docs link to the canonical rule file; no rule is restated
- [ ] Vocabulary matches the detected stack

## References
- `references/interaction-protocol.md` — the per-section preview→approve→build→verify→hand-back loop.
- `references/detection.md` — reading `structure.json`; stack kinds and their vocabulary.
- `references/audience-tree.md` — the audience model and how to reshape it per stack.
- `references/analysis.md` — mapping flows/modules/units from code; the code-vs-docs gap audit.
- `references/conventions.md` — front-matter, foldering, reports-vs-todo, link-don't-restate, git mv.
- `references/section-recipes.md` — how to build each section type.
- `references/verification.md` — what `check_docs.py` checks and what "verified" means.
