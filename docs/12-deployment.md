# 12 - Deployment

![Deployment](diagrams/fig5_deploy.png)

## Local (no Docker)
See the root README: `pip install -r backend/requirements-dev.txt`, train the demo model, run uvicorn on :8000, `npm run dev` on :5173.

## Docker Compose
`cp .env.example .env && docker compose up --build` -> UI http://localhost:8080 (nginx, proxies `/api` to the backend), API http://localhost:8000/docs.
`backend/entrypoint.sh` trains the **synthetic demo model** on first start when `PHISHLENS_AUTO_TRAIN_DEMO=true` (set in compose). Models, stored mail and the SQLite file live in named volumes.
**Not tested here** (no Docker engine in the build environment); the Dockerfiles are straightforward but expect small fixes on first run.
Disable auto-training and mount a real model directory for anything beyond demos.

## Hugging Face Space (free backend)
`Dockerfile.space` builds the backend with build context `backend/`:
```powershell
docker build -f Dockerfile.space -t phishlens-space backend
docker run --rm -p 7860:7860 phishlens-space
```
The Space runs `uvicorn` on port 7860, stores SQLite and raw mail on ephemeral local disk, and trains the synthetic demo model on first start. A real model directory must be mounted or baked in for anything beyond a demo.

`.github/workflows/deploy-space.yml` uploads `backend/` to the Space, writes `Dockerfile.space` as the Space `Dockerfile`, and requires `HF_TOKEN` and `HF_SPACE_ID` secrets. It fails if `/api/health` does not report `model_loaded: true`. The Space is public by default; never send real personal email to it.

## Vercel frontend (free)
`frontend/vercel.json` builds the Vite app and rewrites unknown paths to `index.html` so client routes such as `/cases`
work on refresh. Import the GitHub repository in Vercel, set **Root Directory** to `frontend`, and add
`VITE_API_BASE_URL=https://<space-host>` plus `VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` as Production and Preview
environment variables. `VITE_API_BASE_URL` is read at build time, so changing it requires a redeploy.
On the backend, set `PHISHLENS_CORS_ORIGINS` to the exact Vercel origins (production domain first, preview domains if you
use them). `*` is rejected at startup because credentialed CORS would otherwise mirror any origin.

## Supabase
1. Create a project. 2. Run `supabase/migrations/0001_init.sql` and `0002_auth_hardening.sql` in the SQL editor (tables + RLS). 3. Backend env: `PHISHLENS_DATABASE_URL=postgresql+psycopg://...` (install `requirements-postgres.txt`),
`PHISHLENS_AUTH_MODE=supabase`, and either `PHISHLENS_SUPABASE_JWT_SECRET=<Project Settings -> API -> JWT secret>` (HS256) or `PHISHLENS_SUPABASE_JWKS_URL=https://<project>.supabase.co/auth/v1/.well-known/jwks.json` (RS256/ES256). 4. Frontend build args: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
5. Raw email files: v0.1 writes to local disk (`storage/`); move to Supabase Storage (private bucket) before real use.
Postgres itself is still **not exercised in tests** (tests use SQLite). RLS isolation has a live-only contract test that skips without credentials; see `docs/11-security-privacy.md`.

## Inbound email
Choose a provider that can deliver inbound mail to a webhook (Postmark inbound, Mailgun routes, SendGrid inbound parse, Cloudflare Email Routing + Worker). Point the bot domain's MX at it, set the webhook URL to
`https://<backend>/api/webhooks/inbound` and the shared secret. Write an adapter if the payload is not raw MIME. Gmail API push (OAuth + Pub/Sub) is the later alternative (ADR-002).

## Hosting options (provider not fixed)
Railway / Render / Fly.io (least ceremony for two containers + managed Postgres) or one VM with Docker Compose + Caddy for TLS (cheapest, most control). CI: `.github/workflows/ci.yml` runs backend tests and the frontend build; add an image-build/deploy job once a host is chosen.

## Scaling and the async path
Watch p95 time from "webhook received" to "analysis stored". If SHAP + inference exceed a few seconds under load: webhook enqueues (Redis) and returns 202; a Celery worker runs `analyze`; the UI polls or subscribes via Supabase Realtime. No feature/model/explanation code changes.
