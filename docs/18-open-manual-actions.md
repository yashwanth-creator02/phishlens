# Open manual actions

Everything below needs **you**, because it needs an account, a dashboard click, or a password that the agent cannot
read. Each item states what to do, the exact values to paste, how to know it worked, and what the agent does next.

Rules for this file:

- The agent keeps it current: an item is deleted the moment it is done, not marked complete.
- Last reviewed: 2026-11-13.
- If an item is blocked on the agent instead of you, it does not belong here; it belongs in the project log.

---

## 1. Get a second person's mailbox for the final false-positive test (20 minutes for them)

*(Status: Deferred by user - to be added later)*

**Why:** the model's false-positive rate is currently measured on **your** inbox, which is also part of its training
data. The reviewer's point is that this number cannot be read as a general false-positive rate: the feature set
identifies the mail provider and the era, not only the message (`docs/22-training-methodology-and-measurements.md` has the measurement). A second inbox from
a different provider is the only way to find out whether the number transfers, and it is the final test set - nothing
is tuned on it.

**Steps:** ask a friend or a classmate, with their clear consent, for their legitimate mail. The cleanest route is for
them to run the extraction script locally and send only the feature CSV, never the raw emails:

1. In Google Takeout, select **Mail only** (not Spam or Trash) and download the export. Put the `.mbox` in
   `backend/data/raw/mailbox-second/` - that directory is gitignored, and it must never be committed.
2. Or run the extraction locally and send only the CSV:
   ```powershell
   cd backend
   .\.venv\Scripts\python.exe -m training.profile_corpus --mailbox <path-to-their-export> --out <their-csv>
   ```
   The CSV has one row per message and 65 numbers per row. It contains no text, no addresses and no subjects.

**Their data never enters training.** It is the test set, and it is used once.

**Done when:** the folder `backend/data/raw/mailbox-second/` has the export (or the CSV is handed over), and the
agent can report the false-positive rate at the shipped thresholds on mail the model has never seen.

---

## 2. Give the bot a real email address (30-60 minutes, needs a domain)

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

---

## Already handled - do not redo

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
