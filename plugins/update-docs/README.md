# update-docs

Build, restructure, or gap-fill a project's documentation as an **audience-split tree written from
the code** — proposing the tree first and then working **one approval-gated section at a time**.

Generic and **stack-adaptive**: it detects whether the repo is a mobile app, web app, backend/API,
library, CLI, or monorepo, and adapts both the tree and the vocabulary (screens vs routes vs
endpoints vs public API).

## What it does

1. **Reads the project** — `scan_project.py` detects the stack, source layout, candidate units, and
   an inventory of every existing doc (writing only to a git-excluded `.update-docs/`).
2. **Proposes a docs tree** — an audience split (`how-to` · `architecture` · `dev` · `reference`)
   reshaped for the stack, plus a move-map for any existing docs and the granularity choices that
   matter. **Stops for your approval.**
3. **Builds it section by section** — for each top-level folder: previews what it'll write and from
   which sources → you approve → it writes the docs **from code** (front-matter, cross-links, `git mv`
   for moves) → verifies links with `check_docs.py` → hands it back for you to verify → next.

Handles three situations in one flow: **greenfield** (build fresh), **restructure** (move messy docs
into the tree, fix inbound references), and **gap-fill** (audit code vs docs, add what's missing).

## How it keeps docs honest

- Every doc carries `source` / `verified_at` / `verified_commit` front-matter, so staleness is
  checkable.
- Docs **link** to the repo's canonical rule file (`CLAUDE.md`/`AGENTS.md`/…) instead of restating
  rules.
- `reference/reports/` are dated snapshots, **never edited**; `reference/todo/` are living lists.
- Moves use `git mv` and every inbound reference is repointed in the same step.
- `check_docs.py` fails the section on any broken link or heading anchor.

## Run it

```
/update-docs
```
Then follow the prompts — it will never write or move anything without your approval for that step.

## Layout

```
skills/update-docs/
├── SKILL.md            orchestrator (hard rules + run flow)
├── references/         loaded one at a time: interaction-protocol, detection, audience-tree,
│                       analysis, conventions, section-recipes, verification
└── scripts/
    ├── scan_project.py  structure/stack/units/existing-docs → .update-docs/structure.json
    └── check_docs.py    broken links / anchors / front-matter / stale refs
```

Portable — copy `skills/update-docs/` into any repo's `.claude/skills/` and run it without edits.
