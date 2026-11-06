# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-06.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

## 1. Supabase Auth settings and how to log in (5 minutes)

**Why:** the deployed app has a sign-in screen but no sign-up screen (`Login.tsx` only calls
`signInWithPassword`), and Supabase requires email confirmation by default, which would force every demo user
through a rate-limited confirmation mail. Two different toggles matter:

- **Enable Email provider = ON** (must stay on — turning this off disables email sign-in entirely)
- **Confirm email = OFF** (for the demo; leave on if you later use a real SMTP provider)

**Steps**, in project `vmbtdrmevlovvvfvtqmd` -> **Authentication**:

- **URL Configuration**: Site URL `https://phishlens-gules.vercel.app`; add the same host under Redirect URLs.
- **Sign In / Providers -> Email**: Confirm email off.
- **Users -> Add user**: email + password (minimum 6 characters), with **Auto Confirm User** ticked. Repeat for
  each demo user (up to 10). There is no sign-up UI in the app, so accounts are created here, not on the site.

**Done when:** signing in at https://phishlens-gules.vercel.app/login with the dashboard-created credentials lands
you inside the app and an uploaded `.eml` scores. The Render backend already runs with `PHISHLENS_AUTH_MODE=supabase`
and the JWKS URL, so it verifies the JWT Supabase issues with no further setup.

## 2. Optional: let pushes deploy the frontend (2 minutes)

**Why:** today the site updates only when the agent runs `vercel deploy --prod --yes`; the Vercel GitHub App has no
access to the private repo.

**Steps:** install the Vercel GitHub App on `yashwanth-creator02/phishlens` (Vercel dashboard -> **Add New -> Project**
shows the install link, or GitHub -> Settings -> GitHub Apps). Then tell the agent.

**Done when:** a push to `main` produces a Vercel deployment on its own (the agent runs `vercel git connect` to finish
the link).

## 3. Fallback if Render ever refuses you

If Render asks for a card or blocks the account, say so and the agent will instead expose the local backend through a
cloudflared quick tunnel for the demo. Trade-off: the URL changes on every restart, exists only while your machine and
the tunnel are running, and the Vercel build has to be redeployed each time it changes.

## Already handled - do not redo

- Hugging Face is ruled out as a backend host: Docker Spaces need a paid plan and free ZeroGPU Spaces need an account
  30+ days old. Both attempts returned HTTP 402 on 2026-11-06, so `Dockerfile.space`, `deploy/space/` and the
  `deploy-space` workflow were deleted; `render.yaml` replaces them.
- Vercel project `phishlens` exists, serves https://phishlens-gules.vercel.app, has `VITE_SUPABASE_URL` and
  `VITE_SUPABASE_ANON_KEY` set, and project-level Vercel Authentication is disabled so the URL is public.
- Supabase project `vmbtdrmevlovvvfvtqmd` is active with `0001_init.sql` and `0002_auth_hardening.sql` applied
  (7 tables, RLS on all).
- Both feature branches are merged into `main` and pushed.
- **Backend is live on Render** (`phishlens-api`) at https://phishlens-api-6esn.onrender.com; `/api/health` returns
  `{"status":"ok","model_loaded":true,"auth_mode":"supabase"}`.
- **Frontend is wired to it**: Vercel project `phishlens` carries `VITE_API_BASE_URL=https://phishlens-api-6esn.onrender.com`
  and was redeployed on 2026-11-06; the served bundle references the Render host.
- Render MCP is installed globally (API key via `{env:RENDER_API_KEY}`) and verified working.
