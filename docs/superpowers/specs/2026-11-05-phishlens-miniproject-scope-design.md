# PhishLens mini-project scope and design

Date: 2026-11-05
Status: approved 2026-11-05; extended with a broader frontend surface.

## Intent

A college mini-project submission: an explainable phishing-triage prototype that accepts a suspicious email, scores it, and shows reasons verified against the email. Deadline is the end of November or the first week of December 2026. The team has four members, but two will do the work. Everything must run on free tiers with no credit card. A public demo URL is acceptable, a cold start is acceptable, and up to 10 users need isolated analyses.

## Goals

- Upload-based analysis as the primary path.
- Webhook simulation to prove the pipeline.
- Supabase authentication and per-user isolation.
- Retrain on a real, public corpus and report honest metrics.
- Keep the reason engine evidence-verified.
- Deploy the frontend and backend on free tiers.
- Produce the report, slides, and demo script.

## Non-goals

- Paid services, paid domains, or anything requiring a card.
- Real sensitive email in the public demo.
- Real inbound email as a must-have; Gmail IMAP is a stretch goal.
- Redis, Celery, browser add-on, LLM wording, or a mobile app.
- Claiming synthetic-model metrics as real-world results.

## Constraints

- Three to four weeks, two active contributors. Training time is not the limiting factor; model work can run offline.
- No credit card, no paid tier.
- The Hugging Face Space is public.
- Cold starts of 30 to 60 seconds are acceptable.
- Ten users maximum.
- Repository stays private until submission.

## Approaches considered

1. One VM with Docker Compose: rejected because free no-card options are unreliable and the ops cost is high for two people.
2. Vercel plus Render free: rejected because the 512 MB instance is likely to run out of memory with SHAP and XGBoost.
3. Vercel plus Hugging Face Spaces plus Supabase: chosen. Free, no card, enough RAM, public URL, managed auth and Postgres.
4. Local-only demo: rejected because it does not demonstrate multi-user access or a public URL.

## Architecture

- Frontend: Vercel Hobby, React and Vite, Supabase JS auth, API base URL from an environment variable.
- Backend: Hugging Face Spaces Docker, FastAPI, CORS limited to the frontend origin, secrets stored in Space settings.
- Data: Supabase Auth, Postgres, row-level security keyed by user id, private Storage bucket for raw email.
- Model: trained offline, artifact baked into the Docker image or downloaded from a release; no training inside the container.
- Ingestion: upload first, simulated webhook second, Gmail IMAP only if time allows.
- Build: a GitHub Actions workflow pushes the backend subset to a public Hugging Face Space using an `HF_TOKEN`. The Space source is public; the GitHub repository stays private.
- Model artifact: baked into the image when small enough for a fast cold start, otherwise fetched from a private Hugging Face model repository at boot.

## Builder-check resolutions

1. Data access stays backend-only. FastAPI uses the Supabase service-role connection and scopes every query by the authenticated `user_id`. Isolation is application-enforced. RLS policies are added as defense in depth and tested through a user-scoped JWT, not through the service role; no claim that the service role is constrained by RLS.
2. Local development and the existing tests stay on SQLite. Production uses Postgres. Models use portable SQLAlchemy types, and one Postgres smoke test covers the deployed dialect. Supabase SQL migrations remain authoritative for production.
3. The public Space is fed by GitHub Actions; the private repository is not connected directly. The model is baked into the image to protect the cold-start target.
4. There is no scheduler inside the Space. Retention is an on-demand admin endpoint, optionally called by a weekly GitHub Actions job. Supabase free-tier pausing is handled by a demo-day checklist that wakes the project and the Space before the presentation.
5. Accounts are pre-created, up to ten. Public signup is disabled; the UI has login only.
6. A first-time sender uses the same neutral history defaults as training, and a test covers it. Cold-start senders are reported as a separate evaluation slice.
7. Reported metrics: precision, recall, F1, PR-AUC, false-positive rate at the chosen threshold, calibration, and the cold-start slice. Target is recall of at least 0.85 at a false-positive rate of at most 0.10; if missed, it is reported honestly and not hidden by test-set tuning.
8. Splits are grouped within each corpus: phishing by campaign or URL host, ham by sender. A domain-disjoint split across the two corpora is not used, because it would measure corpus difference rather than generalization. Dedupe by Message-ID and body hash; report grouped and random splits.
9. The webhook endpoint ships disabled unless a strong `WEBHOOK_SECRET` is set. The public demo uses upload; the default `change-me` secret is never accepted in production.

## Data

- Nazario phishing corpus plus SpamAssassin ham; add a larger ham sample such as Enron if its licence allows.
- Commit a download script, a dataset card with counts and licences, and a few sample emails.
- Do not commit raw corpora.
- Split by phishing campaign or URL host, and by ham sender, not randomly.

## Gmail path (stretch)

- Dedicated Gmail account, 2-Step Verification, App Password, IMAP enabled.
- Per-user alias as `bot+<token>@gmail.com`; recover the token from `Delivered-To`.
- Fetch manually from the UI or by a free GitHub Actions schedule.
- Store the App Password only in Space and Actions secrets.
- Use test mail only.

## Security and privacy

- No secrets or corpora in git.
- Isolation is verified two ways: an API test proves one user cannot read another's analysis, and an RLS test uses a user-scoped JWT rather than the service role.
- Enforce request size limits and an on-demand retention endpoint.
- Keep the demo mailbox free of real personal email.
- Make the Space public knowingly; never put real email or credentials in it.

## Work plan

Phase 1, must finish:
- Design approval, dataset card, download script.
- Real corpus training and evaluation.
- Supabase schema, RLS, and auth.
- Upload flow and two-user isolation.
- Vercel and Space deployment.
- Report skeleton and demo script.

Phase 2, should finish:
- Gmail IMAP fetch.
- Retention job.
- Small explanation audit.

Phase 3, stretch:
- Real inbound provider.
- Async queue.

## Verification

- Backend tests pass.
- Frontend builds.
- Health reports the model loaded.
- Upload returns a scored analysis.
- Two users cannot read each other's analyses.
- Public URLs work from a different network.
- Docs and report match observed results.

## Risks

- Free hosts may change limits or sleep unpredictably.
- Real inbound email may not fit the no-card constraint.
- Two active people limit scope; the cut list above is the safety valve.
- Dataset licences must be checked before the repository becomes public.

## Frontend surface

The submission needs more than one screen. Ship these routes and shared overlays:

- `/` dashboard: totals, band counts, recent cases, upload, search, loading, empty, and error states.
- `/cases` full case list: search, band filter, sort, pagination, and per-row link.
- `/cases/:id` case report: verdict, band bar, verified reasons, evidence panels, SHAP table, raw headers, copy summary, and delete.
- `/model` model card: active model, training source, metrics, thresholds, and limitations.
- `/how-it-works` pipeline and feature-group explainer.
- `/settings` profile, forwarding alias, sender baseline, retention, and account actions.
- `/status` API and model health.
- `/login` sign-in only, no public signup.
- `*` not-found page.

Shared overlays: delete confirmation, sign-out confirmation, session-expired dialog, toast notifications, and an upload progress state.

Navigation stays in the app shell. Every page has a clear heading, a back path, keyboard focus, and a mobile layout.

## Plan

`docs/superpowers/plans/2026-11-05-phishlens-miniproject.md`

## Open decisions

- Exact submission date.
- Which dataset versions and licences.
- Report template and required sections.

