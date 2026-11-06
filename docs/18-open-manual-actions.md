# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-06.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

## 1. Optional: send the demo through the real model (15 minutes, on your machine)

**Why:** the Render service runs the synthetic demo model, so uploaded `.eml` files score against generated data, not
the Nazario and SpamAssassin corpora your evaluation measured. Promoting the corpora-trained model into the image is
the one remaining upgrade that changes what the live demo reports. The evaluation and the model already exist and are
reproducible from `docs/19-teammate-training-guide.md`; this is the promote step.

Read the warning in step 7 of that guide first: on the corpora-trained model the two `legit_*.eml` demo samples
score HIGH, because SpamAssassin's 2003 ham has no `Authentication-Results` headers while those samples do. Decide
whether to accept that for the demo or keep the demo on the synthetic model.

**Steps**, in `backend/` with the venv from the README:

```powershell
python -m training.download_datasets       # pulls the five Nazario mboxes and two SpamAssassin tarballs
python -m training.evaluate --out reports  # reproduces the 0.987 grouped F1 / 0.998 PR-AUC report
python -m training.train --source corpus --phish-dir data/raw/nazario --legit-dir data/raw/spamassassin --out models --reports reports
```

Then make the two-part change from step 8 of the guide (copy the model in `backend/Dockerfile`, set
`PHISHLENS_AUTO_TRAIN_DEMO=false` in `render.yaml`), commit the model and both files, and push: Render rebuilds on
`main`, the image no longer trains the demo model at build time, and `/api/health` will name the promoted model.
Paste in chat only the final model ID.

**Done when:** the site shows scores from the corpora-trained model; tell the agent and it will verify `/api/health`
names that model.

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
- **Vercel is linked to the repo** (user installed the GitHub App; pushes now deploy on their own).
- **Supabase Auth is configured**: Site URL set, Confirm email off, demo users seeded from the dashboard, and the
  deployed sign-in works end to end.
