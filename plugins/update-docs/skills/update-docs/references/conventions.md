# Conventions — how every doc is written

## Front-matter (every doc)

```yaml
---
source: <the code path(s) this doc mirrors>
verified_at: <YYYY-MM-DD>
verified_commit: <short hash at write time>
---
```

`source` is the code that, if it moves, makes the doc stale — a script can compare `git log` on
`source` against `verified_commit` to flag drift. Get the hash from `git rev-parse --short HEAD` at
write time. Add `status:` when useful (e.g. `moved from <old>; not fully re-verified`, or
`skeleton — needs <input>`). **Snapshots** in `reports/` are stamped instead with a banner (below)
and their original date.

## Foldering

One folder per topic, the main file named after it: `architecture/module-wise/checkout/checkout.md`
(+ any companion in the same folder). Keeps a topic's files together so same-folder links survive a
move. Category folders that hold flat single-file docs (a `project-setup/`, a `reports/`) are fine —
don't over-fold.

## reports/ vs todo/ (living vs frozen)

- **`reports/`** — dated, point-in-time: audits, migration write-ups, root-cause notes, feasibility
  calls. Each carries, as the first line after front-matter:
  `> **Snapshot — not maintained.** Written ~<date>. Kept as evidence, not current truth.`
  **Never edited.** A new investigation is a new file. Other docs cite them ("per the April audit"),
  never as current truth. This is also where a **living doc retires** — move it here and date it,
  rather than deleting it or letting it rot in place.
- **`todo/`** — living action lists / tracked tech-debt, meant to be edited and ticked. The opposite
  of `reports/`. (Quick tasks belong in the team tracker; `todo/` is for durable, in-repo lists with
  analysis worth keeping beside the code.)

## Link, don't restate

The canonical rule file (`CLAUDE.md` / `AGENTS.md` / `CONTRIBUTING.md` / `README`) is the single
source of truth for coding rules. Docs **link** to it and explain the *why*; they never copy a rule.
A rule appearing in both places is a bug. Likewise, docs link across sections per the ownership rule
(`audience-tree.md`) rather than duplicating prose.

## Moving existing docs

- Use **`git mv`** so history follows the file (rename detection survives adding front-matter).
- **Fix every inbound reference in the same commit/step** — code comments, CI config, other skills,
  READMEs, and cross-doc links. A moved doc with a live reference to its old path breaks tooling
  silently. Grep the whole repo (and any sibling skills/CI) for the old path.
- Recompute relative links when a file's depth changes (resolve old target → new path → relative).
- A holding area (e.g. `docs/legacy/`) is a fine temporary parking spot during a big restructure —
  but the run isn't done until it's emptied and removed.

## What not to write

- No hand-written props/prop-type/param tables — fastest-rotting content; generate or omit.
- No secrets, tokens, or `.env` values, ever.
- No invented behavior — see hard rule 1.
- Exclude generated/mirrored trees (like `code-mirror/`) from any code-indexing ignore file so a
  graph/search tool doesn't return both the source and its paraphrase.
