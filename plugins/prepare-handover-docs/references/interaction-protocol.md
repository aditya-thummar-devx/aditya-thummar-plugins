# Interaction protocol (how every run behaves)

This is the contract for the whole skill. Both variants follow it. The user must stay
in control: **nothing is written to Google without an explicit confirmation for that
specific tab.**

## Upfront (once)

1. **Detect the project** (load the matching `detection-*.md`). Determine the app
   display name, bundle id / package, versions, whether Firebase is present, and which
   env files exist. State the git branch, commit, and whether the tree is dirty.
2. **Confirm the app name** you will use everywhere (offer the detected value, let the
   user correct it). Use only that project's real identity — never a placeholder or an
   example project's name.
3. **Show the tab list** you will create (default six). **Ask the user to add or
   remove** tabs. If no Firebase config files were found, offer to drop the Firebase tab.
4. **Target doc**: ask for an existing doc id, or tell the user to create a new empty
   Google Doc and share edit access to the token's identity, then give you its id.
5. **Token**: ask for the OAuth token (load `token-guide.md` and walk them through it
   if they don't have one). Confirm it has `documents` + `drive` scope.

## Per tab, in fixed order (Env → Firebase → App Store → Play Store → Release & Rollback → Overview last)

1. **Announce the step.** State which tab this is and, in two short lists, exactly what
   it will include: *auto-derived from the repo* vs *needs you*. No surprises.
2. **Gather.** Auto-discover the repo facts (per the detection reference). Then ask the
   user for the values only they have, and ask "**anything to add or remove for this
   tab?**". Do not ask for anything you can read from the repo.
3. **Draft.** Write the spec to `docs/handover/specs/<tab>.json` (target project).
   Run the engine with `--dry-run` and confirm the self-check passes. Show a **sign-off
   view** — a compact human summary of what the tab will say, and call out any
   `PENDING_*` placeholders still needing a value.
4. **Stop for confirmation.** Do not proceed until the user approves the content.
5. **Prepare to write.** Ask whether the token is still valid; if a prior write 401'd or
   time has passed, ask for a fresh token. Otherwise ask permission to write.
6. **Duplicate guard.** Read the doc's existing tabs. If a tab with this title already
   exists, tell the user to delete it in the Docs tab sidebar first (the API cannot
   delete tabs), then continue.
7. **Write.** Run the engine live (`--doc <id>`). Report the new tab id.
8. **Verify.** Re-read the tab and confirm the **last spec block's text is present** in
   it. If it is missing, the write truncated — tell the user, have them delete the tab,
   and regenerate. Do not claim success on an unverified tail.
9. **Hand back.** Stop and ask the user to open the tab, verify it, and confirm before
   moving to the next tab.

## Editing a tab already written

The engine only appends and the Docs API has no tab-delete. To change a tab: edit the
spec, have the user **delete the existing tab** in the sidebar, then regenerate. Tab
titles must be unique, so a regenerate over an undeleted tab fails.

## Tone

Terse and concrete. One line per clean fact. Show the navigation path when you need the
user to fetch something (a console screen, a Drive link). Never predict store approval;
report the status as observed.
