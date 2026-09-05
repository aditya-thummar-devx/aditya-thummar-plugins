# Verification — what "done" means for a section

Never claim a section is done on unverified links. Run the checker, fix what it flags, then hand back.

## The checker

```
python3 scripts/check_docs.py <docs-dir> [--stale-path <old-dir>] [--strict]
```

Checks four things across the tree:
- **broken links** — a relative `.md`/`.mdx` link whose target file doesn't exist (**hard fail**).
- **broken anchors** — a link to a `#heading` (same-file or cross-file) whose slug doesn't exist,
  using the GitHub slug rule (**hard fail**).
- **missing front-matter** — a doc that doesn't start with `---` (warning; `--strict` fails it).
- **stale refs** — with `--stale-path legacy` (say), links whose target still points into the old
  location (warning; `--strict` fails it). Use this during a restructure so nothing links back into
  the holding area.

Exit non-zero on any hard fail (or any warning under `--strict`). It's read-only.

## How to use it per section

- After building/moving a section, run it on the whole `docs/` tree (links cross sections). Fix
  every broken link and anchor before hand-back.
- During a restructure, always pass `--stale-path <holding-dir>` and drive it to zero — a link back
  into the parked copy is the classic silent breakage.
- At the close, run it once more over the whole tree, plus:

## Checks the script can't do — do these by hand

- **Front-matter present on every doc** (the script warns; confirm it's zero).
- **Inbound references outside `docs/`** repointed — grep the repo, CI files, and sibling
  skills for any moved path. The script only sees links *inside* the docs tree.
- **`git status --find-renames`** shows moves as renames (history preserved), not delete+add.
- **Accuracy spot-check** — read one or two of the densest new docs against their `source` files;
  a doc that passes the link check can still be wrong about the code.
- **No secrets** landed in any doc.

A named remaining gap at the close is honest and fine. A silent broken link is not.
