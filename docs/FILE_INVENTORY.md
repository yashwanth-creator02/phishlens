# File inventory

What each tracked path is for. Update this file in the same change that adds, moves, renames, or deletes a tracked
file; a stale inventory is worse than none because it sends the next reader to the wrong place.

Generated or downloaded content is deliberately absent: `backend/.venv/`, `backend/models/`, `backend/storage/`,
`backend/reports/`, `backend/data/raw/` (corpora), `frontend/node_modules/`, `frontend/dist/`,
`frontend/test-results/`, local `*.db` files, and `.tmp/`.

## Repository root

| Path | Purpose |
|---|---|
| `README.md` | Project front door: what it is, quick start, honest limits |
| `AGENTS.md` | Agent instructions, commands, invariants, verification checklist, known gaps |
| `Makefile` | Cross-platform convenience targets (`setup`, `train-demo`, `backend`, `frontend`, `test`, `build`, `up`) |
| `docker-compose.yml` | API + UI container stack (untested in this environment) |
| `Dockerfile.space` | Container for the Hugging Face Space build |
| `backend.ps1` / `frontend.ps1` | Windows launchers; `backend.ps1` refuses a Python older than 3.11 |
| `.env.example` | Compose-level environment template (Docker paths, not local paths) |
| `.gitignore` | Excludes virtualenvs, models, storage, DBs, Playwright output, graphify cache |

## `backend/app/` - FastAPI service

| Path | Purpose |
|---|---|
| `main.py` | App factory, CORS middleware, router wiring |
| `schemas.py` | Pydantic request/response models |
| `api/analyses.py` | List, detail, features, upload, delete endpoints; bounded chunked upload reads |
| `api/webhooks.py` | Forwarded-email webhook: secret check, alias lookup, bounded body read |
| `api/deps.py` | Auth dependency (disabled / Supabase JWT), current-user resolution |
| `core/config.py` | `PHISHLENS_*` settings, CORS origin validation (wildcard rejected) |
| `db/models.py` | SQLAlchemy tables: analyses, features, explanations, sender profiles |
| `db/repository.py` | Owner-scoped queries, transactional delete, retention purge |
| `db/session.py` | Engine and session factory (SQLite locally, PostgreSQL in deployment) |
| `ingestion/email_parser.py` | Direct, inline-forwarded, and `message/rfc822` attachment parsing; header normalisation |
| `features/feature_vector.py` | The shared 57-feature vector used by training and serving |
| `features/{header,url,text,action,attachment,behavioral}_features.py` | One module per feature group |
| `features/{common,lexicons}.py` | Shared helpers and the urgency/credential word lists |
| `ml/registry.py` | Model loading plus metadata validation (feature names and order) |
| `explain/shap_engine.py` | SHAP contributions for the active model |
| `explain/reasons.py` | Candidate reason selection and evidence verification |
| `explain/templates.py` | Plain-language sentence templates per feature |
| `scoring/risk_bands.py` | Probability to 0-100 score and Low/Medium/High band |
| `services/analysis_service.py` | The end-to-end pipeline: parse, predict, explain, persist, update history |

## `backend/training/` and `backend/scripts/`

| Path | Purpose |
|---|---|
| `training/synthetic.py` | Generated demo corpus (pipeline checks only) |
| `training/corpus.py` | Real corpus loading with grouped split keys (URL host, sender domain) |
| `training/download_datasets.py` | Nazario + SpamAssassin fetch with SHA-256 manifests |
| `training/train.py` | Training entry point, model selection, calibration, reports |
| `training/evaluate.py` | Grouped-split evaluation, cold start, random-split baseline |
| `scripts/verify_rls.py` | Live Supabase RLS isolation check in both directions |

## `backend/tests/`

| Path | Purpose |
|---|---|
| `conftest.py` | App/client fixtures; trains a small synthetic model once per session |
| `test_parser.py` | Three forwarding shapes; inline forward marks authentication missing |
| `test_features.py` | Feature count and order, phishing vs legitimate behaviour, behavioural thresholds |
| `test_reasons_and_bands.py` | Evidence-verified reasons, discard rules, fallback, band edges |
| `test_api.py` | Endpoints, upload limits, webhook secret/alias, history pollution, isolation |
| `test_auth_supabase.py` | JWT verification paths, 401 handling |
| `test_cors.py` | Configured origin allowed, unknown origin rejected, wildcard refused |
| `test_retention_and_cold_start.py` | Transactional delete, purge, neutral cold start |
| `test_evaluate.py` | Grouped-split evaluation harness on fixtures |
| `test_corpus_loading.py` | Extensionless hash-named corpus files and mbox-plus-loose-file loading |
| `test_download_datasets.py` | Archive fetch, checksum manifest, idempotent reruns, tar traversal rejection |
| `test_rls_contract.py` | Live-only PostgreSQL RLS contract (skips without credentials) |

## `backend/data/sample_emails/`

Four demo messages used by the UI and the tests: PayPal phish, invoice phish forwarded inline, legitimate newsletter,
legitimate bank alert.

## `frontend/`

| Path | Purpose |
|---|---|
| `src/App.tsx` | Routes, `RequireAuth`, session provider wiring |
| `src/auth.tsx` | Supabase session context |
| `src/supabase.ts` | Client construction from `VITE_SUPABASE_*` |
| `src/api/client.ts` | `apiFetch`: base URL, bearer token, typed errors |
| `src/types.ts` | Response types shared across pages |
| `src/lib/cases.ts` | Search, filter, sort, pagination helpers (unit tested) |
| `src/pages/Dashboard.tsx` | Upload, counters, band cards, recent cases |
| `src/pages/AnalysisDetail.tsx` | Band bar, verified reasons, SHAP table, features, delete |
| `src/pages/Cases.tsx` | Case queue with filters and pagination |
| `src/pages/Model.tsx` | Active model identity and metrics with the synthetic-data caveat |
| `src/pages/HowItWorks.tsx` | Pipeline and feature-group explanation |
| `src/pages/Status.tsx` | Health and model-loaded state |
| `src/pages/Settings.tsx` | Forwarding alias and environment notices |
| `src/pages/Login.tsx` | Sign-in, or an explicit authentication-disabled notice |
| `src/components/` | `AppShell`, `BandBar`, `ConfirmDialog`, `EvidencePanel`, `FeatureTable`, `ReasonCard`, `RiskBadge`, `SessionExpired`, `Toast`, `UploadBox` |
| `src/styles.css`, `src/styles/*.css` | Design tokens, shell, report, and status styles |
| `src/test/setup.ts` | Vitest setup (Testing Library matchers, jsdom cleanup) |
| `e2e/smoke.spec.ts` | Playwright smoke: unauthenticated check plus signed-in journey |
| `playwright.config.ts` | Chromium project, dev-server boot, `E2E_BASE_URL` support |
| `vite.config.ts` | Dev proxy to `:8000`, Vitest config limited to `src/**` |
| `vercel.json` | Vercel build settings and SPA rewrite |
| `nginx.conf`, `Dockerfile` | Container build for the compose stack |
| `.env.example` | `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

## `supabase/migrations/`

| Path | Purpose |
|---|---|
| `0001_init.sql` | Tables, indexes, RLS enablement |
| `0002_auth_hardening.sql` | Idempotent policy hardening for the authenticated role |

## `docs/`

| Path | Purpose |
|---|---|
| `README.md` | Documentation index |
| `01`-`15` | Topic docs: overview, project log, plan, architecture, backend, frontend, data model, ML, explainability, API, security, deployment, testing, user study, risks |
| `16-demo-script.md` | Review walkthrough with expected screens and fallbacks |
| `17-real-corpus-evaluation.md` | Measured Nazario + SpamAssassin results, grouped split, caveats |
| `decisions/ADR-001`-`014` | Decision records |
| `report/01`-`04` | Long-form report chapters |
| `report/final-report.md` | Submission write-up: objectives, implementation, verified results, limits |
| `report/_sources/` | Generator scripts for the report chapters |
| `diagrams/` | Mermaid sources plus rendered PNGs |
| `screenshots/` | UI captures used in docs and the deck |
| `presentation/` | Review-1 deck and the script that edits it |
| `datasets/README.md` | Corpus provenance and licensing notes |
| `original/` | First project idea and early architecture notes |
| `superpowers/specs/`, `superpowers/plans/` | Mini-project scope design and the task plan it produced |
| `demo_training_report_SYNTHETIC.md` | Recorded demo-model training output |
| `frontend_refinement_report.md` | UI overhaul notes |

## Other

| Path | Purpose |
|---|---|
| `.github/workflows/ci.yml` | Backend tests plus frontend build on push |
| `.github/workflows/deploy-space.yml` | Upload to the Space, then fail unless `/api/health` reports the model loaded |
| `scripts/send_sample.py` | Simulates a forwarded-email webhook |
| `scripts/purge_old.py` | Retention purge helper |
| `deploy/space/README.md` | Space configuration and secrets |
| `graphify-out/` | Code knowledge graph (regenerate with `graphify extract . --code-only`) |
