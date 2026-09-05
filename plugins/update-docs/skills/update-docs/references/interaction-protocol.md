# Interaction protocol (how every run behaves)

The contract for the whole skill. The user stays in control: **nothing is written or moved
without an explicit approval for that specific step.** Two gates bracket every section — one before
(approve the plan), one after (verify the result).

## Upfront (once)

1. **Read the project** — run `scan_project.py`, read `structure.json`. State branch, commit, and
   whether the tree is dirty. If dirty, say which files, and ask whether to proceed or let the user
   settle the tree first (docs off a dirty tree can be wrong).
2. **Confirm the detected stack** — offer the detected kind/framework and let the user correct it
   before anything is built on top of a misread.
3. **Propose the tree** — show it, say who each section is for, show a move map for a restructure,
   and surface the granularity forks with a recommendation each. **Ask, don't assume.** Iterate to
   a final tree the user approves. Write nothing until then.

## Per section, in the approved order

1. **Preview / announce.** State which section this is and, in two short lists, exactly what it
   will include: *auto-derived from the repo* vs *needs you*. Name the source files each doc reads.
   No surprises.
2. **Stop for approval.** Do not build until the user approves this section's plan.
3. **Build.** Explore the code (subagents for breadth), then write from code — front-matter,
   foldering, cross-links, link to the canonical rule file. For a restructure, `git mv` each
   existing doc and fix its inbound references in the same step.
4. **Verify.** Run `check_docs.py` on the section (with `--stale-path` during a restructure). Fix
   everything it reports. Show the result. Never claim done on unverified links.
5. **Hand back.** Stop and ask the user to open the section, verify it reads true, and confirm
   before the next section.

## Editing a section already handed back

Treat it like any other change: preview the edit, get approval, make it, re-verify, hand back.
Never silently rewrite a section the user already signed off.

## Tone

Terse and concrete. One line per clean fact. When you need the user to fetch something outside the
repo, give the exact path/navigation. State what you actually read; never predict, never pad a
thin section with invented findings.
