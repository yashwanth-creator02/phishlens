# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-13.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

---

## 1. Test against a second independent mailbox for the final false-positive test

*(Status: Deferred by user - to be added later)*

**Why:** the model's false-positive rate is currently measured on the primary inbox, which is also part of its training
data. The reviewer's point is that this number cannot be read as a general false-positive rate: the feature set
identifies the mail provider and the era, not only the message (`docs/22-training-methodology-and-measurements.md` has the measurement). A second inbox from
a different provider is the only way to find out whether the number transfers, and it is the final test set - nothing
is tuned on it.

**Steps:** obtain an independent second mailbox export. The cleanest route is to run the extraction script locally and produce only the feature CSV, never raw emails:

1. In Google Takeout or another provider export, select **Mail only** (not Spam or Trash) and place the `.mbox` in
   `backend/data/raw/mailbox-second/` - that directory is gitignored, and it must never be committed.
2. Or run the extraction locally and save only the CSV:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m training.profile_corpus --mailbox <path-to-export> --out <feature-csv>
   ```
   The CSV has one row per message and 65 numbers per row. It contains no text, no addresses and no subjects.

**This data never enters training.** It is strictly a holdout test set, used once.

**Done when:** the folder `backend/data/raw/mailbox-second/` has the export (or the CSV is handed over), and the
agent can report the false-positive rate at the shipped thresholds on mail the model has never seen.

---

## Already handled - do not redo

- **Inbound Email Forwarding via Cloudflare & Worker**: Domain `phislens.dpdns.org` delegated to Cloudflare DNS, Email Routing catch-all configured to Worker `phishlens-inbound`, forwarding raw emails with `X-Recipient` and `X-Webhook-Secret` to Render API `/api/webhooks/inbound`. `GET /api/forwarding` returns `alias_domain: "phislens.dpdns.org"` and `inbound_configured: true`. Documented in `docs/23-cloudflare-email-forwarding.md`.
- **Docker Desktop & WSL2 Engine**: Windows host restarted and verified. Docker engine is running; local `docker build -f backend/Dockerfile -t phishlens-api backend` builds cleanly, and the containerized model loads and serves the 65-feature release model. Line endings in `entrypoint.sh` enforced as LF via `.gitattributes`.
- **Phishing Pot Licence Terms (CC BY-NC 4.0)**: Acceptance confirmed by owner on 2026-11-13 for academic non-commercial research use; recorded in `docs/datasets/README.md`.
- **Google OAuth Sign-In**: Client ID and secret created in Google Cloud Console with authorized origins (`https://phishlens-gules.vercel.app`, `http://localhost:5173`) and redirect URI (`https://vmbtdrmevlovvvfvtqmd.supabase.co/auth/v1/callback`), and configured in Supabase Auth.
- **Anonymous Sign-in**: Enabled in Supabase Auth dashboard; guest authentication is active on the login page.
- **The signed-in Playwright journey runs against production.** Both E2E tests pass against the live URL with an
  account you supply (`npm run test:e2e`).
- Hugging Face is ruled out as a backend host (HTTP 402 on free tiers); Render free tier web service via `render.yaml` serves the backend.
- Vercel project `phishlens` serves https://phishlens-gules.vercel.app with automatic git deploy.
- Supabase project `vmbtdrmevlovvvfvtqmd` is active with RLS and schemas applied.
- **The released model is in `backend/release/model/`** (`xgboost-corpus-20261112-s7`). It passed the privacy audit with 0 findings and 0 personal rows in the SHAP background sample.
- **Backend is live on Render** (`phishlens-api`) at https://phishlens-api-6esn.onrender.com.
- **Frontend is wired to it**: Vercel `VITE_API_BASE_URL` points to the Render host.
- Render MCP is installed globally and verified working.
- **Supabase Auth is configured**: Confirm email is enabled; confirmed accounts receive aliases via `GET /api/me/alias`.
- **Forwarding status published**: `GET /api/forwarding` accurately returns inbound configuration status.
