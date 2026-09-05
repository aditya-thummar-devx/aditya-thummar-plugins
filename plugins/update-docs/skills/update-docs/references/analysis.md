# Analysis — mapping real units and finding gaps

The scan gives candidate piles. This is how you turn them into the real units to document, and how
you find what's undocumented. Do this with **subagents** for breadth (many files, one conclusion),
not by reading every file into the main thread.

## Find the real units (not the candidates)

Read the **registry**, not the folder names:
- **Screens/routes** — the router / navigation config (`routesConfig`, `RootStack`, `pages/` router,
  `routes.rb`, a route table). It lists the real reachable units; the `candidateUnits` list will
  have extras (helper components named `...Screen`, `pages/` dirs that aren't routes) and sometimes
  misses one. Trust the registry.
- **Endpoints** — the route/controller registration (`@Get`/`@Post`, `app.get`, url patterns, a
  router mount). Group by resource/service.
- **Modules/flows** — a "flow" is behavior that spans 2+ units: checkout, auth, a booking→payment→
  confirm chain, a data-sync pipeline. Find them by following what a unit *calls* (shared hooks,
  stores, services, API folders), not by folder membership.
- **Public API (library)** — the package entry (`main`/`exports`, `index.*`, `__all__`) — the
  surface consumers actually import.

For each unit/flow capture, with `path:line`: what it is (one line), its entry point, the
state/data it touches, the API/services it calls, and any non-obvious gotcha. That capture *is* the
doc's raw material — keep it tight.

## The code-vs-docs gap audit (gap-fill mode)

To find what's undocumented, diff **real units** against **documented units**:
1. List real units from the registries above.
2. List documented units from `structure.json.existingDocs` (which screen/route/module docs exist).
3. The difference is the gap. Rank it: a whole user-facing flow with no doc outranks a single
   utility screen; a payment/auth path outranks a static page.
4. Also flag **thin** docs (a flow doc that covers only its entry screen) and **stale** docs (whose
   `verified_commit` is far behind, if front-matter is present).

Report the gap as a list *before* proposing docs for it — let the user pick scope (all of it, the
top few, a named subset). Don't silently document everything.

## Rules while analyzing

- **Confirm before claiming.** If you can't find where something is wired, say "couldn't locate the
  registration" — never assert a unit exists because a file is named suggestively.
- **Cite as you go.** A flow you can't cite you can't document; drop it or mark it TODO.
- **Note code-health observations** you trip over (a fallback that disagrees with its comment, dead
  code, debug logs) and surface them to the user — but they're observations, not doc content.
