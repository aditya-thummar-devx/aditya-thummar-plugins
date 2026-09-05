# Getting the OAuth token (step by step)

The engine writes to the Google Doc as *you*, using a short-lived OAuth access token you
paste in. It is never stored; it lives only in the one command that writes a tab.

## Fastest path — OAuth 2.0 Playground

1. Open **https://developers.google.com/oauthplayground**.
2. In the left panel ("Step 1 — Select & authorize APIs"), paste these two scopes into
   the "Input your own scopes" box (one per line, or space-separated):
   ```
   https://www.googleapis.com/auth/documents
   https://www.googleapis.com/auth/drive
   ```
   - `documents` is required (writes the tabs).
   - `drive` is required only if you embed screenshots, but include it anyway — it is
     harmless and saves a re-mint later.
3. Click **Authorize APIs**, then sign in with the Google account that **owns or can
   edit** the target doc, and approve.
4. In "Step 2", click **Exchange authorization code for tokens**.
5. Copy the **Access token** (starts with `ya29.`). That is the token to paste when the
   skill asks.

## Notes

- **Lifetime ~1 hour.** If a write fails with `401 UNAUTHENTICATED`, the token expired —
  mint a fresh one and paste it. The skill will ask.
- The token identity must have **edit access** to the target doc. For a brand-new doc,
  create it while signed in as that same account (simplest), or share edit access to it.
- Any token source works (a service-account-minted token, a `gcloud` token, etc.) — the
  engine only needs the bearer string with the two scopes above.
- Never commit or paste the token anywhere but the skill prompt.
