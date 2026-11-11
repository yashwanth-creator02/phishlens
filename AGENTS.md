# PhishLens project instructions

## What this project is

PhishLens is an explainable phishing-triage prototype. A user forwards a suspicious email; the backend parses it, extracts 65 features in six groups, scores it with a calibrated tree/linear model, turns SHAP contributions into plain-language reasons, verifies each reason against evidence found in the email, and returns a Low / Medium / High risk band. The React UI shows the result and the supporting evidence.

Status: v0.2 working skeleton. The extractor is 65 features. The released model
(`xgboost-corpus-20261111-s7`, in `backend/release/model/`) is an XGBoost fitted on the owner's
mailbox plus Nazario pre-2024 phishing and SpamAssassin 2003 ham; it passed the privacy audit
(0 findings) and measures FPR 0.022 at probability 0.5 on 2,865 held-out legitimate messages from
2026, with phishing recall 0.810 on 788 held-out phishing messages. It is fitted on one inbox and on
a 20-year-old phishing corpus, so those numbers describe that combination and not real-world
detection. See `docs/21-modern-corpus-evaluation-plan.md`.

## Stack

- Backend: Python 3.11+ (CI and Docker use 3.12), FastAPI, SQLAlchemy 2, Pydantic Settings, scikit-learn, XGBoost, SHAP, joblib.
- Frontend: React 18, TypeScript, Vite 5, optional Supabase authentication.
- Data: SQLite by default for local development; PostgreSQL/Supabase schema in `supabase/migrations/`.
- Packaging: Docker Compose, Makefiles, GitHub Actions.

## Repository layout

| Path | Purpose |
|---|---|
| `backend/app/` | FastAPI app, API routes, config, DB models/repository, ingestion, feature extraction, model registry, SHAP reasons, risk bands, analysis service |
| `backend/training/` | Synthetic/corpus data generation and model training entry point |
| `backend/tests/` | Pytest suite (86 pass; one live-only Supabase RLS test skips without credentials) |
| `backend/release/` | The audited model the Docker image serves; empty until a release passes the privacy audit |
| `backend/data/sample_emails/` | Demo `.eml` files used by the UI and tests |
| `frontend/src/` | React pages, components, typed API client |
| `frontend/e2e/` | Playwright smoke suite (`npm run test:e2e`) |
| `supabase/migrations/` | PostgreSQL schema and Row-Level-Security policies |
| `docs/` | Project overview, architecture, API, ML, security, report, ADRs, diagrams, presentation |
| `scripts/` | Webhook simulation and retention purge helpers |

## Local setup (Windows PowerShell)

The default `python` on this machine is 3.10, which is too old because the training code imports `datetime.UTC`. Use `py -3.11` or newer.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m training.train --source synthetic --n 2400 --out models --reports reports
python -m pytest -q
python -m uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and upload a file from `backend/data/sample_emails/`. API health is at http://localhost:8000/api/health and OpenAPI docs at http://localhost:8000/docs.

`backend/.venv/`, `backend/models/`, `backend/storage/`, `backend/reports/`, `frontend/node_modules/`, `frontend/dist/`, and local `*.db` files are generated and must not be committed.

## Configuration

Settings come from environment variables with the `PHISHLENS_` prefix, loaded from `backend/.env` when present. Defaults are development-safe only:

- `DATABASE_URL=sqlite:///./phishlens.db`
- `AUTH_MODE=disabled`, `DEV_USER_ID=dev-user`
- `WEBHOOK_SECRET=change-me`
- `MODEL_DIR=./models`, `STORAGE_DIR=./storage`
- `BAND_LOW_MAX=29`, `BAND_HIGH_MIN=70`

`.env.example` is written for Docker Compose (its database path is `/app/data_db/...`). Do not copy it for local development without changing `PHISHLENS_DATABASE_URL`. Never commit any `.env` file. Set a real webhook secret and enable authentication before exposing the service.

## Pipeline and invariants

1. Parse the email (direct, forwarded inline, or forwarded as a `message/rfc822` attachment).
2. Load the sender history profile.
3. Extract the shared 65-feature vector from six groups: header, URL, text, action, attachment, behavioral.
4. Predict with the active model and optional isotonic calibration.
5. Convert probability to a 0-100 score and a band.
6. Compute SHAP contributions.
7. Build reasons; a reason is shown only if its evidence rule verifies against the parsed email. If a Medium/High result has no verified reason, use the generic fallback reason.
8. Persist the analysis, raw-email metadata, all feature values, and explanations.
9. Update sender history only when the result is Low risk.

Non-negotiable invariants:

- Training and serving must use the same feature names and order. The model registry rejects mismatched metadata.
- Attachments are metadata only. Never open, execute, or render them.
- Inline forwarding loses the original SPF/DKIM/DMARC headers; represent them as missing, not failed.
- Do not claim model quality from the synthetic demo model.
- A model fitted on a personal mailbox is derived from private data. It may reach a committed artifact or the public
  deployment only after `backend/scripts/audit_model.py` reports the artifact clean and the owner has explicitly
  decided. `backend/scripts/release_model.py` performs both steps together.
- Keep the reason engine evidence-verified; do not emit a specific claim that the email does not support.
- Do not change the feature set, thresholds, or reason rules without updating tests and the relevant `docs/` page.

## Commands

From the repository root on Windows:

```powershell
.\backend.ps1   # API on :8000 (uses backend\.venv; requires Python 3.11+)
.\frontend.ps1  # UI on :5173 (uses frontend\node_modules)
```

```powershell
# Train on a real corpus
python -m training.train --source corpus --phish-dir C:\data\nazario --legit-dir C:\data\spamassassin_ham --out models

# Score a model on modern mail (evaluation only; never writes a model)
python -m training.evaluate_modern --model-dir models --phish-dir data/raw/nazario --out reports/modern

# Privacy audit before publishing a model (required for any model fitted on a personal mailbox)
python -m scripts.audit_model --model models/active --mailbox data/raw/mailbox

# Run the suite
python -m pytest -q

# Docker (not verified in this environment)
copy .env.example .env
docker compose up --build

# Backend image alone (also what Render builds; bakes the synthetic demo model)
docker build -f backend/Dockerfile -t phishlens-api backend
```

Root `make` targets: `setup`, `train-demo`, `backend`, `frontend`, `test`, `build`, `up`. On Windows, prefer the explicit PowerShell commands unless `make` is installed.

## Working rules

- Create a branch for every feature, fix, or refactor. Do not commit directly to `main` after the initial import. Do not merge into `main` without explicit user approval; use `git merge --no-ff` when approved.
- Commit and push completed work. If no remote exists, stop and report that rather than inventing one.
- Update `README.md` and the relevant `docs/` files in the same change as code. Keep documentation honest about what is tested and what is not.
- Keep `docs/18-open-manual-actions.md` current: it lists only work blocked on the user. Add an item when a step needs an account, dashboard, or password the agent cannot reach; delete it the moment it is done; never leave a completed item in the list.
- Add or update tests for behavior changes; keep the existing suite green.
- Prefer deterministic scripts over ad-hoc manual steps. Put temporary artifacts in `.tmp/` and never commit them.
- No emojis in code, comments, logs, UI, documentation, or commit messages.
- Stop dev servers and release ports/background processes before finishing a task.

## Verification checklist

Before reporting work as done:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# GET /api/health must report model_loaded true
cd ..\frontend
npm test
npm run test:e2e
npm run build
```

Also upload at least one sample email through the UI or API and confirm a scored analysis is returned. Check that generated artifacts remain untracked.

## Known gaps

- Real-corpus evaluation is measured on 2003-2007 research corpora with one grouped split and no confidence interval
  (grouped F1 0.948, PR-AUC 0.990; see `docs/17-real-corpus-evaluation.md`). It does not validate the shipped model.
- The corpora-trained model **does not work on modern legitimate mail**: FPR 0.999 on 2,216 received messages from a
  real 2020-2026 inbox, and removing the era features does not fix it. Cause, ablation and options are in
  `docs/21-modern-corpus-evaluation-plan.md`; do not quote an accuracy claim for modern mail.
- The released model is personal-data-derived and **misses three of its own promotion gates**: domain-macro FPR 0.112
  against 0.10, recall 0.810 against 0.90, Brier 0.039 against 0.02. The measurement is in
  `docs/21-modern-corpus-evaluation-plan.md` section 16; any claim about it must carry those numbers.
- No real inbound-email provider or domain-age lookup yet.
- Corpora are gitignored; `python -m training.download_datasets` (from `backend/`) fetches them. Both the manifest writer
  and `corpus.load_dir` accept extensionless files on purpose: SpamAssassin stores hash-named messages, and a suffix
  filter silently drops every legitimate sample.
- Docker Compose has not been exercised in this environment.
- The frontend is live on Vercel (https://phishlens-gules.vercel.app) with `VITE_API_BASE_URL` pointing at the Render
  backend, and the backend is live on Render (`phishlens-api`, https://phishlens-api-6esn.onrender.com). Both
  auto-deploy on a push to `main`. The deployed backend serves the released model from `backend/release/model/`.
- Hugging Face hosting is ruled out: Docker Spaces need a paid plan and free ZeroGPU Spaces need a 30-day-old account
  (HTTP 402 on both). The backend target is now Render's free Docker web service via `render.yaml` (512 MB, 0.1 CPU,
  sleeps after 15 idle minutes). Peak RSS for one demo analysis measured ~257 MB locally.
- The frontend has Vitest coverage for the API client, case helpers, shell, login, and feature table, and a Playwright
  smoke suite whose signed-in journey needs seeded credentials; there is no linter.
- `requirements.lock.txt` exists but is not used by install, CI, or Docker targets.
- The report references `docs/original/synopsis_mini_project_phishlens.docx`, which is not present in the repository.
- The frontend dependency audit reports known Vite, esbuild, and React Router advisories whose fixes are major-version upgrades.
