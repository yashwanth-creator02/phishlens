# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-12.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

The 2026-11-12 work needed nothing from you. The Kaggle corpora were ingested, the candidate that the protocol
picked was released through the privacy audit (`backend/scripts/release_model.py`, 0 findings), and Render rebuilt and
now serves it (`xgboost-corpus-20261112-s7`).

## 1. Restart Windows once, so Docker's engine can start (2 minutes)

**Why:** Docker Desktop 4.99 is installed, and its Linux engine needs WSL2. The two Windows optional features it
requires were enabled on 2026-11-12, but enabling them only takes effect after a restart, so the engine still reports
`Virtual Machine Platform not enabled` and `docker build` fails with a 500 from the Linux engine.

**Steps:** restart Windows. Nothing else. If Docker Desktop does not start itself, open it and wait for the engine to
report "running".

**Done when:** `docker version` prints a `Server:` line, and this works:

```powershell
docker build -f backend/Dockerfile -t phishlens-api backend
```

**Why it is optional:** the deployed backend does not depend on the local build. Render builds the same Dockerfile on
the same base image, and that is what runs in production.

## 2. Optional: restore push-to-deploy for the backend (2 minutes)

**Why:** the `phishlens-api` service already has `autoDeploy = yes` and the `main` push rebuilt it once; this is now
just housekeeping. The one thing it cannot do is the first step, which is already done.

**Steps:** none required. If the Render GitHub App ever loses repo access, re-install it at render.com ->
**Add New -> Blueprint** and pick `yashwanth-creator02/phishlens`, branch `main`.

**Done when:** a push to `main` produces a new Render build on its own (it already does).

## 3. Fallback if Render ever refuses you

If Render asks for a card or blocks the account, say so and the agent will instead expose the local backend through a
cloudflared quick tunnel for the demo. Trade-off: the URL changes on every restart, exists only while your machine and
the tunnel are running, and the Vercel build has to be redeployed each time it changes.

## 4. Rotate the published E2E test account password (2 minutes)

**Why:** the shared test account `e2e@phishlens.test` and its password were written into two documentation pages
while this repository was public, so the password has been readable by anyone. The account only ever held test
traffic and no analyses, but a credential for a live hosted auth service should not sit in a public history.

**Steps:** Supabase dashboard -> Authentication -> Users -> `e2e@phishlens.test` -> set a new password, or delete
the account and create your own. Then set the new values in your shell before running the E2E suite:

```powershell
$env:E2E_EMAIL = "e2e@phishlens.test"
$env:E2E_PASSWORD = "<the new password>"
```

**Done when:** `npm run test:e2e` passes with the new password and the old one no longer signs in.

**Note:** the password literal has been removed from the docs, but it remains in the git history of those two files.
Rotating it is what makes the old value worthless; rewriting the history is not needed.

## 5. Turn on "Confirm email" in Supabase and give the backend the anon key (5 minutes)

**Why:** a forwarding alias is a capability - whoever holds it puts mail into that account's history - so it is now
issued only to an account whose email address is confirmed. The backend enforces this itself, but two Supabase
settings have to be in place first.

**Steps:**

1. Supabase dashboard -> Authentication -> Sign In / Providers -> Email -> turn **Confirm email** on. With it on,
   GoTrue refuses to issue a session to an unconfirmed address, so an unconfirmed account cannot sign in at all.
2. Supabase dashboard -> Project Settings -> API -> copy the **anon** key (the `anon` public key, not the
   `service_role` key).
3. Render dashboard -> `phishlens-api` -> Environment -> add `PHISHLENS_SUPABASE_ANON_KEY` with that value and save.
   The API base URL is derived from the JWKS URL the service already has, so there is nothing else to set.
4. Send yourself a confirmation email from the sign-up screen, open it, and confirm. The account then signs in and
   `GET /api/me/alias` returns the forwarding address.

**Done when:** `curl https://phishlens-api-6esn.onrender.com/api/health` reports `auth_mode: supabase`, a confirmed
account can sign in on https://phishlens-gules.vercel.app and see its forwarding address on the Profile screen, and an
unconfirmed account gets a "verify your email" message instead of an address.

**Note:** until step 3 is done, `GET /api/me/alias` answers 503 ("Email verification is not configured"). That is the
intended failure mode - it fails closed rather than handing an alias to an unverified account.

## Already handled - do not redo

- **The signed-in Playwright journey runs against production.** Both E2E tests pass against the live URL with an
  account you supply. The credentials are deliberately not in this repository:
  ```powershell
  cd frontend
  $env:E2E_BASE_URL = "https://phishlens-gules.vercel.app"
  $env:E2E_EMAIL = "<your Supabase account>"
  $env:E2E_PASSWORD = "<its password>"
  npm run test:e2e
  ```
  Create the account in Supabase Auth, or rotate the old shared test account as described in item 4. The account
  holds no analyses and is only used by the test; delete it from the Supabase dashboard once the project is
  submitted and the tests no longer need to run against the live deployment.
- Hugging Face is ruled out as a backend host: Docker Spaces need a paid plan and free ZeroGPU Spaces need an account
  30+ days old. Both attempts returned HTTP 402 on 2026-11-06, so `Dockerfile.space`, `deploy/space/` and the
  `deploy-space` workflow were deleted; `render.yaml` replaces them.
- Vercel project `phishlens` exists, serves https://phishlens-gules.vercel.app, has `VITE_SUPABASE_URL` and
  `VITE_SUPABASE_ANON_KEY` set, and project-level Vercel Authentication is disabled so the URL is public.
- Supabase project `vmbtdrmevlovvvfvtqmd` is active with `0001_init.sql` and `0002_auth_hardening.sql` applied
  (7 tables, RLS on all).
- The dashboard-UI, real-corpus-evaluation and modern-corpus branches are all merged into `main` and pushed. `main`
  is at the merge that carries the released model.
- **The released model is in `backend/release/model/`** (`xgboost-corpus-20261112-s7`). It passed the privacy audit:
  395 sender domains, 400 distinctive subject words, 0 findings, and 0 personal rows in the SHAP background sample. The
  result is recorded in `backend/release/model/release.json`. The Docker image copies it into `/app/models/active/`, so
  the next Render build serves it.
- **Backend is live on Render** (`phishlens-api`) at https://phishlens-api-6esn.onrender.com; `/api/health` returns
  `{"status":"ok","model_loaded":true,"auth_mode":"supabase"}`.
- **Frontend is wired to it**: Vercel project `phishlens` carries `VITE_API_BASE_URL=https://phishlens-api-6esn.onrender.com`
  and was redeployed on 2026-11-06; the served bundle references the Render host.
- Render MCP is installed globally (API key via `{env:RENDER_API_KEY}`) and verified working.
- **Vercel is linked to the repo** (user installed the GitHub App; pushes now deploy on their own).
- **Supabase Auth is configured**: Site URL set, Confirm email off, demo users seeded from the dashboard, and the
  deployed sign-in works end to end.
