# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-11.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

No new owner-only action came out of the 2026-11-11 decision on the modern-mail story. The four-candidate protocol
ran on 2026-11-11, candidate D was retrained with the current code, and it was released through the privacy audit
(`backend/scripts/release_model.py`, 0 findings). Nothing below needs you until a replacement model is wanted.

## 1. Optional: restore push-to-deploy for the backend (2 minutes)

**Why:** the `phishlens-api` service already has `autoDeploy = yes` and the `main` push rebuilt it once; this is now
just housekeeping. The one thing it cannot do is the first step, which is already done.

**Steps:** none required. If the Render GitHub App ever loses repo access, re-install it at render.com ->
**Add New -> Blueprint** and pick `yashwanth-creator02/phishlens`, branch `main`.

**Done when:** a push to `main` produces a new Render build on its own (it already does).

## 2. Fallback if Render ever refuses you

If Render asks for a card or blocks the account, say so and the agent will instead expose the local backend through a
cloudflared quick tunnel for the demo. Trade-off: the URL changes on every restart, exists only while your machine and
the tunnel are running, and the Vercel build has to be redeployed each time it changes.

## Already handled - do not redo

- **The signed-in Playwright journey runs against production.** A dedicated test account
  `e2e@phishlens.test` exists in Supabase Auth, and both E2E tests pass against the live URL:
  ```powershell
  cd frontend
  $env:E2E_BASE_URL = "https://phishlens-gules.vercel.app"
  $env:E2E_EMAIL = "e2e@phishlens.test"
  $env:E2E_PASSWORD = "phishlens-e2e-2026"
  npm run test:e2e
  ```
  The account holds no analyses and is only used by the test. The password is a throwaway that exists
  so the suite can run unattended; delete the account from the Supabase dashboard if the project is
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
- **The released model is in `backend/release/model/`** (`xgboost-corpus-20261111-s7`). It passed the privacy audit:
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
