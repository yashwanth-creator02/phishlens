# 12 - Deployment

![Deployment](diagrams/fig5_deploy.png)

## Local (no Docker)
See the root README: `pip install -r backend/requirements-dev.txt`, train the demo model, run uvicorn on :8000, `npm run dev` on :5173.

## Docker Compose
`cp .env.example .env && docker compose up --build` -> UI http://localhost:8080 (nginx, proxies `/api` to the backend), API http://localhost:8000/docs.
`backend/entrypoint.sh` trains the **synthetic demo model** on first start when `PHISHLENS_AUTO_TRAIN_DEMO=true` (set in compose). Models, stored mail and the SQLite file live in named volumes.
**Not tested here** (no Docker engine in the build environment); the Dockerfiles are straightforward but expect small fixes on first run.
Disable auto-training and mount a real model directory for anything beyond demos.

## Supabase
1. Create a project. 2. Run `supabase/migrations/0001_init.sql` in the SQL editor (tables + RLS). 3. Backend env: `PHISHLENS_DATABASE_URL=postgresql+psycopg://...` (install `requirements-postgres.txt`),
`PHISHLENS_AUTH_MODE=supabase`, `PHISHLENS_SUPABASE_JWT_SECRET=<Project Settings -> API -> JWT secret>`. 4. Frontend build args: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
5. Raw email files: v0.1 writes to local disk (`storage/`); move to Supabase Storage (private bucket) before real use.
Postgres + RLS were **not exercised in tests** (tests use SQLite).

## Inbound email
Choose a provider that can deliver inbound mail to a webhook (Postmark inbound, Mailgun routes, SendGrid inbound parse, Cloudflare Email Routing + Worker). Point the bot domain's MX at it, set the webhook URL to
`https://<backend>/api/webhooks/inbound` and the shared secret. Write an adapter if the payload is not raw MIME. Gmail API push (OAuth + Pub/Sub) is the later alternative (ADR-002).

## Hosting options (provider not fixed)
Railway / Render / Fly.io (least ceremony for two containers + managed Postgres) or one VM with Docker Compose + Caddy for TLS (cheapest, most control). CI: `.github/workflows/ci.yml` runs backend tests and the frontend build; add an image-build/deploy job once a host is chosen.

## Scaling and the async path
Watch p95 time from "webhook received" to "analysis stored". If SHAP + inference exceed a few seconds under load: webhook enqueues (Redis) and returns 202; a Celery worker runs `analyze`; the UI polls or subscribes via Supabase Realtime. No feature/model/explanation code changes.
