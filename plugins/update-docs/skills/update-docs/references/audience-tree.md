# Audience tree — the model and how to reshape it

Docs are split **by audience** at the top level, and **living docs are separated from dated
snapshots**. A content editor, a new developer, and someone chasing a past decision should each land
in a different place, not one flat list.

## The skeleton (default)

```
docs/
├── README.md          entry point — what lives where, who each section is for
├── how-to/            non-technical: operating the product (only if there IS a non-tech surface)
├── architecture/      technical: how the product works, feature-first
│   ├── <units>/       one doc per screen / route / endpoint (thin; links into modules)
│   └── modules/       one doc per cross-unit domain/flow (owns the prose)
├── dev/               how to set up and work in the codebase
│   ├── getting-started, setup, conventions-pointer
│   ├── recipes/       task-first "how do I add a X" (links to the canonical rule file + tools)
│   └── code-mirror/   structural map of the source tree (excluded from any code index)
└── reference/         lookup + history (not a reading path)
    ├── <specs>/       live specs kept current
    ├── reports/       dated snapshots — NEVER edited (audits, migrations, feasibility)
    └── todo/          living action lists / tracked tech-debt (the opposite of reports/)
```

## Reshape per stack (`detection.md` kinds)

- **mobile-app / web-app** — `architecture/` = screen|route-wise (thin) + `modules/` (flows). Add
  `how-to/` only if there's a non-technical surface (a CMS, an admin, content editors).
- **backend-api** — `architecture/` = `endpoints/` + `services/`; add `reference/api/` (the endpoint
  contract) and `reference/data-model/`. Usually **no** `how-to/`.
- **library** — lead with `getting-started` + `reference/api/` (the public surface) + `guides/`;
  `architecture/` covers internals. Drop `how-to/`.
- **cli** — `usage/` + `recipes/` + `reference/commands/`.
- **monorepo** — per `detection.md`: a tree per package, or a routing top-level.

**Drop sections that don't apply.** A pure library has no content editors, so no `how-to/`. Adding
an empty audience folder is worse than omitting it. Let the analysis and the user decide which
survive.

## Ownership rule (avoids drift)

When two sections could hold the same thing, **one owns the prose and the other links in**:
- `modules/` (or `services/`) owns cross-unit flow prose; the per-unit doc stays thin and links to it.
- `code-mirror/` is **structural** (what each folder/file is) and links to `architecture/` for
  behavior — it never re-explains a flow.
- `reference/` holds the spec; `architecture/` explains how it's used and links to the spec.
State ownership in `README.md` / the section index so a reader knows which doc is the source of truth.

## Granularity forks to put to the user

- **Code mirror depth** — one index per folder (~dozens of docs, low upkeep) vs a page per file
  (hundreds; owes a doc edit per source change — usually not worth it). Recommend folder-level.
- **Which flows get their own module doc** — every cross-unit flow, or only the top few. Recommend
  the ones that span 2+ units or carry money/auth/state.
- **How-to inclusion** — only if a non-technical operating surface exists.
