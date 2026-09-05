# Detection — reading the scan, choosing vocabulary

`scan_project.py` writes `.update-docs/structure.json`. Read it; don't re-derive the layout by hand.

## Fields that matter

- `scan` — branch/commit/dirty/scannedAt. State this to the user; a stale/dirty read makes wrong docs.
- `stack.kind` — the coarse project kind (below). `stack.frameworks`, `stack.languages`, `manifests`.
- `topLevelSourceDirs` — the real source roots (`src`, `app`, `lib`, `packages`, …).
- `candidateUnits` — `{modules, screens, routes, endpoints}`. **Candidates, not truth.** They are
  heuristic piles to point your code-reading at; over-inclusion is expected (a component named
  `...Screen` or a `pages/` dir may not be a route). Confirm real units by reading routing/registry
  code (Step in `analysis.md`), never by trusting this list.
- `entryPoints` — where execution starts (`index.js`, `main.py`, `App.tsx`, `cmd/`…).
- `conventionFiles` — canonical rule files (`CLAUDE.md`/`AGENTS.md`/`CONTRIBUTING.md`/`README`). Docs
  **link** to these; never restate them.
- `existingDocs` — every markdown file with `hasFrontMatter`. This decides the mode and drives the
  restructure move-map. Nothing here may be orphaned.

## Kinds → vocabulary (adapt everything you write)

| `kind` | Units you document | Words to use | Extra sections likely |
| --- | --- | --- | --- |
| `mobile-app` | screens + cross-screen modules | screen, flow, navigation | how-to (if CMS/content-driven) |
| `web-app` | routes/pages + modules | route, page, view, component | how-to (content/CMS) |
| `backend-api` | endpoints + services | endpoint, handler, service, job | API reference, data model |
| `library` | public API + guides | export, API, usage | getting-started, API reference |
| `cli` | commands + subsystems | command, subcommand, flag | usage, recipes |
| `monorepo` | packages, then per-package | package, workspace | per-package trees |
| `unknown` | top-level source dirs as modules | module | ask the user to characterize it |

If detection looks wrong (e.g. a Next.js app read as `library`), **say so in Step 1** and let the
user correct the kind before proposing a tree. Everything downstream inherits this choice.

## Monorepo note

For `monorepo`, treat each package under `packages/`/`apps/` as its own project: either one docs
tree per package, or a top-level tree that routes into per-package sections. Propose both and let
the user pick.
