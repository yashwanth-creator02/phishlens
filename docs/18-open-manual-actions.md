# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-11.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

## 1. Decide the modern-mail story (the only open modelling decision)

**Why:** the corpora-trained model was measured on 2,216 messages from your own inbox and flags **99.9%** of them
as phishing (2,202 HIGH, 12 MEDIUM, 2 LOW). The cause is that the only legitimate mail in the training data is
SpamAssassin 2003, which has no authentication headers at all, so the model reads "authenticated mail" as
"phishing". Removing the authentication features does not fix it (measured: FPR@0.29 stays at 0.93-0.97 for every
ablation variant). The full evidence is in [21](21-modern-corpus-evaluation-plan.md) section 7.1.

**Recommendation:** keep the synthetic demo model in the deployment, keep the corpora model as a documented
historical artefact, and publish no accuracy claim for modern mail. That is honest, and it is the strongest story for
a viva: a measured failure, its root cause, and the evidence that closing it needs data you do not have.

**Your call, if you want the model to work on modern mail** - each option needs something only you can do:

1. **Allow a modern legitimate-mail source for training.** The only real modern ham available is a mailbox export
   like the Takeout file you already provided, which is currently evaluation-only. Say so explicitly and the
   pipeline already knows how to read it. The risk to state in the report: the model would then be partly trained
   on one person's mail.
2. **Provide a public modern ham corpus** you have access to (a licensed export from a provider, a shared
   research corpus). There is no free one: the SpamAssassin public corpus ends at 2005, and the modern
   "spam/ham" datasets that claim realistic 2024-2025 headers state on their own data card that the mail is
   generated, so they cannot be evidence of real-world accuracy.
3. **Accept a synthetic-augmented model.** The repository can generate modern-looking legitimate mail and train on
   it. It would stop the false alarms, but it cannot be used to claim accuracy, and it has to be labelled as such
   everywhere.

**Steps:** reply with the option you want, or with "recommendation". Nothing else is needed from you for the
recommendation path.

**Done when:** you have answered, and the agent updates [21](21-modern-corpus-evaluation-plan.md) section 13 and
the risk list to match.

## 2. Delete the mailbox-derived cache (2 minutes, on your machine)

**Why:** the evaluation wrote matrices derived from your inbox into the working folder, and they are personal data.
The raw export itself is at `backend/data/raw/mailbox/All mail Including Spam and Trash.mbox` and is gitignored, but
it is still on disk.

**Steps**, from the repository root:

```powershell
Remove-Item -Recurse -Force .tmp\auth_cache
Remove-Item -Force .tmp\auth_blind.out, .tmp\auth_blind.err
```

Keep or delete `backend/data/raw/mailbox/All mail Including Spam and Trash.mbox` as you prefer; deleting it does not
remove the aggregate numbers already written into the docs, because no message content was ever recorded there.

**Done when:** tell the agent, and it verifies `git status --porcelain` shows no data or report artifact.

## 3. Do not promote the corpora-trained model to the live demo (no action needed, for the record)

This used to be item 1 in this list. It is not an action any more: promoting the corpus model would put a model that
flags every legitimate message behind the live demo, so the recommendation is to leave the synthetic demo model in
the image. If you later decide to promote anyway, the steps are in [19](19-teammate-training-guide.md) step 8, and
the training command now needs `--activate`, which is explicit.

## 4. Optional: restore push-to-deploy for the backend (2 minutes)

**Why:** the `phishlens-api` service already has `autoDeploy = yes` and the `main` push rebuilt it once; this is now
just housekeeping. The one thing it cannot do is the first step, which is already done.

**Steps:** none required. If the Render GitHub App ever loses repo access, re-install it at render.com ->
**Add New -> Blueprint** and pick `yashwanth-creator02/phishlens`, branch `main`.

**Done when:** a push to `main` produces a new Render build on its own (it already does).

## 5. Fallback if Render ever refuses you

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
