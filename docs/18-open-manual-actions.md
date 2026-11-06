# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-06.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

## 1. Create the backend Space (blocks the entire demo)

**Why:** the frontend is live at https://phishlens-gules.vercel.app, but there is no backend to call. Sign-in works,
every analysis request fails. About 10 minutes of work.

**Steps**

1. Sign in at huggingface.co, then **New Space**:
   - name `phishlens-api`, SDK **Docker**, template **Blank**, visibility **Public**, hardware **CPU basic (free)**.
   - The Space ID becomes `<your-username>/phishlens-api`; note it exactly.
2. Create a write token: **Settings -> Access Tokens -> New token**, role **write**.
3. In the GitHub repo (`yashwanth-creator02/phishlens`) add two **Actions secrets**
   (Settings -> Secrets and variables -> Actions):
   - `HF_TOKEN` = the token from step 2
   - `HF_SPACE_ID` = `<your-username>/phishlens-api`
4. In the Space: **Settings -> Variables and secrets**, add these as **secrets**:
   - `PHISHLENS_AUTH_MODE` = `supabase`
   - `PHISHLENS_SUPABASE_JWKS_URL` = `https://vmbtdrmevlovvvfvtqmd.supabase.co/auth/v1/.well-known/jwks.json`
   - `PHISHLENS_DATABASE_URL` = the Supabase **Session pooler** string for `vmbtdrmevlovvvfvtqmd` with
     `postgresql+psycopg://` at the front and your database password filled in, e.g.
     `postgresql+psycopg://postgres.vmbtdrmevlovvvfvtqmd:PASSWORD@aws-0-eu-west-1.pooler.supabase.com:6543/postgres`
     (Supabase dashboard -> **Connect** shows the host; if the password is unknown, **Project Settings -> Database ->
     Reset database password** first).
   - `PHISHLENS_CORS_ORIGINS` = `https://phishlens-gules.vercel.app`
   - `PHISHLENS_WEBHOOK_SECRET` = a random string you generate once
   - optional `PHISHLENS_ADMIN_TOKEN` = another random string, needed only for `POST /api/admin/purge`
5. Trigger the deploy: GitHub -> **Actions -> deploy-space -> Run workflow** on `main`, and wait for green. The
   workflow uploads `backend/` and `Dockerfile.space`, and the Space trains the synthetic demo model on first boot
   (that is why `models/` is not uploaded).
6. Send the agent the Space URL: `https://<your-username>-phishlens-api.hf.space` (dashes, all lowercase).

**Done when:** `https://<space-url>/api/health` returns JSON with `"model_loaded": true`. The agent then sets
`VITE_API_BASE_URL` on the Vercel project, redeploys, and proves an upload-scored round trip.

**Do not** send real personal email to the public Space; the bundled model is a synthetic demo.

## 2. Supabase Auth settings (5 minutes)

**Why:** the deployed app can render the sign-in form but email confirmation is on by default, so every new signup
depends on a confirmation mail from Supabase's rate-limited built-in SMTP.

**Steps**, in project `vmbtdrmevlovvvfvtqmd` -> **Authentication**:

- **URL Configuration**: Site URL `https://phishlens-gules.vercel.app`; add the same host under Redirect URLs.
- **Sign In / Providers -> Email**: turn **Confirm email** off for the demo (leave it on if you intend to use a real
  SMTP provider).

**Done when:** signing up on the deployed URL lands you inside the app without a mail step.

## 3. Optional: let pushes deploy the frontend (2 minutes)

**Why:** today the site updates only when the agent runs `vercel deploy --prod --yes`; the Vercel GitHub App has no
access to the private repo.

**Steps:** install the Vercel GitHub App on `yashwanth-creator02/phishlens` (Vercel dashboard -> **Add New -> Project**
shows the install link, or GitHub -> Settings -> GitHub Apps). Then tell the agent.

**Done when:** a push to `main` produces a Vercel deployment on its own (the agent runs `vercel git connect` to finish
the link).

## 4. Optional: decide the backend path if you skip the Space

If you would rather not create a Hugging Face account, say so and the agent will instead expose the local backend
through a cloudflared quick tunnel for the demo. Trade-off: the URL changes on every restart and exists only while
your machine and the tunnel are running.

## Already handled - do not redo

- Vercel project `phishlens` exists, serves https://phishlens-gules.vercel.app, has `VITE_SUPABASE_URL` and
  `VITE_SUPABASE_ANON_KEY` set, and project-level Vercel Authentication is disabled so the URL is public.
- Supabase project `vmbtdrmevlovvvfvtqmd` is active with `0001_init.sql` and `0002_auth_hardening.sql` applied
  (7 tables, RLS on all).
- Both feature branches are merged into `main` and pushed.
