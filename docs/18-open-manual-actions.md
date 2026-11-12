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

## 1. Confirm acceptance of Phishing Pot licence terms (CC BY-NC 4.0) (1 minute)

**Why:** Using the Phishing Pot corpus (`rf-peixoto/phishing_pot`) requires attribution and is licensed under CC BY-NC 4.0 (Non-Commercial). Before using this data for training or inclusion in a released model, the user must confirm that the project is non-commercial and that attribution will be included.

**Steps:** Review the repository at https://github.com/rf-peixoto/phishing_pot and confirm acceptance of CC BY-NC 4.0 terms.

**Done when:** You confirm acceptance to the agent.

## 2. Restart Windows once, so Docker's engine can start (2 minutes)

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

## 4. Enable anonymous sign-ins in Supabase (1 minute)

**Why:** the login screen now has a "Try it as a guest" button. Supabase refuses to create an anonymous session
until this provider is switched on, so the button currently fails with "Anonymous sign-ins are disabled".

**Steps:** Supabase dashboard -> Authentication -> Sign In / Providers -> **Anonymous** -> tick **Enable anonymous
sign-ins** -> Save.

**Done when:** https://phishlens-gules.vercel.app shows "Try it as a guest", clicking it signs you in, and the
Profile screen says "Guest account" instead of asking you to verify an email. A guest can upload and triage
emails, and correctly gets no forwarding address, because there is no confirmed email to own one.

**Already done by the agent:** the button and the guest-aware Profile panel are built and unit-tested
(`frontend/src/pages/Login.test.tsx`, `frontend/src/pages/Profile.test.tsx`).

## 5. Turn on Google sign-in (10 minutes)

**Why:** the login screen has a "Continue with Google" button, but Google sign-in needs OAuth credentials that
only you can create, because they belong to your Google account. Until they exist, the button returns Google's
"provider not enabled" error.

**Steps:**

1. Google Cloud Console -> create a project (or use an existing one) -> **APIs & Services -> OAuth consent
   screen**. Set the app name, choose **External**, add your own address as a test user, and save.
2. **Credentials -> Create Credentials -> OAuth client ID -> Web application.** Authorised redirect URI:
   `https://<project-ref>.supabase.co/auth/v1/callback`. Authorised JavaScript origin: your app origin
   (`https://phishlens-gules.vercel.app`, and `http://localhost:5173` for local development).
3. Copy the **Client ID** and **Client secret**.
4. Supabase dashboard -> Authentication -> Sign In / Providers -> **Google** -> tick **Enable Google** -> paste the
   client ID and secret -> Save.
5. Supabase dashboard -> Authentication -> URL Configuration -> **Redirect URLs** -> add
   `https://phishlens-gules.vercel.app` and `http://localhost:5173`.

**Done when:** "Continue with Google" on https://phishlens-gules.vercel.app sends you to Google and back, signed
in, with the six screens visible.

**Already done by the agent:** the button, its error handling and its unit test are in place; the backend needs no
change, because a Google session is a normal Supabase JWT and is verified by the same path as a password sign-in.

## 6. Give the bot a real email address (30-60 minutes, needs a domain)

**Why:** the alias domain is still the placeholder `phishlens.example`, which is not a real mailbox, so
forwarding a suspicious email does not reach the system yet. This is the last piece of the forwarding path, and
it is the one thing that needs a domain you own and an account on an inbound-email provider.

**Steps:**

1. Buy a domain (or use one you already own). It only needs to receive mail.
2. Pick an inbound provider that can POST the raw message to a webhook: **Mailgun routes**, **Postmark inbound**,
   **SendGrid inbound parse**, or **Cloudflare Email Routing plus a Worker**. Any of them works; the system only
   needs `POST /api/webhooks/inbound` with the raw RFC-5322 message.
3. Point the domain's MX records at that provider, and set the provider's webhook to
   `https://phishlens-api-6esn.onrender.com/api/webhooks/inbound` with the shared secret in the
   `X-Webhook-Secret` header. The secret is the value of `PHISHLENS_WEBHOOK_SECRET` on the Render service.
4. Set the domain on Render: `PHISHLENS_ALIAS_DOMAIN=<your domain>` (for example `phishlens.app`). Save and let
   Render redeploy.

**Done when:** `GET /api/forwarding` reports your domain and `inbound_configured: true`, and forwarding a test
email to `u-<token>@<your domain>` appears in the account's history within seconds.

**Already done by the agent:** the alias flow, the per-account address, the webhook endpoint with its secret
check, and `GET /api/forwarding`, which publishes the domain and the address pattern for the login screen. The
login screen already tells a visitor when inbound forwarding is not connected, so nobody is misled in the
meantime.

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
  Create the account in Supabase Auth, or use the shared test account, whose password was rotated on 2026-11-12
  because it had been published in an earlier commit of this public repository. The account holds no analyses and is
  only used by the test; delete it from the Supabase dashboard once the project is submitted and the tests no longer
  need to run against the live deployment.
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
- **Supabase Auth is configured**: Site URL set, **Confirm email is on** (turned on 2026-11-12, and verified: a
  confirmed account now gets `200` and a real forwarding address from `GET /api/me/alias`), demo users seeded from
  the dashboard, and the deployed sign-in works end to end.
- **Authentication is on in local development too.** `PHISHLENS_AUTH_MODE` now defaults to `supabase` and the
  public Supabase values (project URL, anon key, JWKS URL) are the defaults in `backend/app/core/config.py` and
  `frontend/src/supabase.ts`. A local checkout therefore exercises the real sign-in, verification and isolation
  paths instead of a single-user bypass. `PHISHLENS_AUTH_MODE=disabled` still exists as an opt-out.
- **The forwarding (bot) address is published for visitors.** `GET /api/forwarding` returns the alias domain, the
  address pattern and whether inbound mail is connected, and the login screen shows it. The per-account token is
  never published; the address appears on the Profile screen after sign-in.
