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
| `render.yaml` | Render blueprint: one free Docker web service for the backend, with its env vars |
| `backend/pyproject.toml` | Backend project metadata, including the `requires-python = ">=3.11"` floor |
| `scripts/check_contrast.py` | WCAG contrast check for the light and dark token sets; composites translucent backgrounds over the surface |
| `backend.ps1` / `frontend.ps1` | Windows launchers; `backend.ps1` refuses a Python older than 3.11 |
| `.env.example` | Compose-level environment template (Docker paths, not local paths) |
| `.gitignore` | Excludes virtualenvs, models, storage, DBs, Playwright output, graphify cache and machine state |

## `backend/app/` - FastAPI service

| Path | Purpose |
|---|---|
| `main.py` | App factory, CORS middleware, router wiring |
| `schemas.py` | Pydantic request/response models |
| `api/analyses.py` | List, detail, features, upload, delete endpoints; bounded chunked upload reads; the forwarding-domain endpoint |
| `api/webhooks.py` | Forwarded-email webhook: secret check, alias lookup, bounded body read |
| `api/deps.py` | Auth dependency (disabled / Supabase JWT), current-user resolution |
| `api/limits.py` | Shared request-size caps for the upload and inbound-webhook paths |
| `core/config.py` | `PHISHLENS_*` settings, CORS origin validation (wildcard rejected) |
| `core/auth.py` | Caller identity and the email-confirmation check that gates a forwarding alias |
| `db/models.py` | SQLAlchemy tables: analyses, features, explanations, sender profiles |
| `db/repository.py` | Owner-scoped queries, transactional delete, retention purge |
| `db/session.py` | Engine and session factory (SQLite locally, PostgreSQL in deployment) |
| `ingestion/email_parser.py` | Direct, inline-forwarded, and `message/rfc822` attachment parsing; header normalisation |
| `features/feature_vector.py` | The shared 65-feature vector used by training and serving |
| `features/{header,url,text,action,attachment,behavioral}_features.py` | One module per feature group |
| `features/{common,lexicons}.py` | Shared helpers and the urgency/credential word lists |
| `ml/registry.py` | Model loading plus metadata validation (feature names and order) |
| `explain/shap_engine.py` | SHAP contributions for the active model |
| `explain/reasons.py` | Candidate reason selection and evidence verification |
| `explain/templates.py` | Plain-language sentence templates per feature |
| `explain/faithfulness.py` | Deletion and stability checks: do the reasons name the features that moved the score, and does a reformatted message keep its verdict |
| `scoring/risk_bands.py` | Probability to 0-100 score and Low/Medium/High band |
| `services/analysis_service.py` | The end-to-end pipeline: parse, predict, explain, persist, update history |
| `services/raw_storage.py` | Raw .eml payload storage: Supabase Storage bucket 'raw_emails' with local filesystem fallback and batch purge |

## `backend/training/` and `backend/scripts/`

| Path | Purpose |
|---|---|
| `training/synthetic.py` | Generated demo corpus (pipeline checks only) |
| `training/corpus.py` | Real corpus loading with grouped split keys (campaign for phishing, sender domain for legitimate mail) |
| `training/download_datasets.py` | Nazario + SpamAssassin fetch with SHA-256 manifests |
| `training/download_kaggle.py` | Kaggle CSV corpora rebuilt as `.eml`, CSV verified against a recorded SHA-256 |
| `training/download_phishing_pot.py` | Phishing Pot fetch, Date header filter, and phishing@pot shortcut masking |
| `training/train.py` | Training entry point, model selection, calibration, reports; takes several corpus directories; the temporal split, the validation-set operating points and the seed sweep live here |
| `training/format_features.py` | The format-only fingerprint of a message - header names, Date and Message-ID shape, charset, MIME structure, line endings, Received-chain length - used to find a provider shortcut |
| `training/evaluate.py` | Grouped-split evaluation, cold start, random-split baseline |
| `training/evaluate_modern.py` | Modern-mailbox evaluation with leakage guard and dual thresholds |
| `scripts/verify_rls.py` | Live Supabase RLS isolation check in both directions |
| `scripts/audit_model.py` | Publish gate: scans a model directory for sender domains, addresses and subject words |
| `scripts/release_model.py` | Audits a candidate, then copies it into `backend/release/model/` |
| `scripts/source_leak_test.py` | Measures whether the feature set identifies the corpus a legitimate email came from, and what that is worth as a cross-corpus false-positive rate |
| `scripts/released_model_importances.py` | Gain share of the released model, and how much sits in the provider/era features |
| `release/model/` | The audited model the Docker image serves; empty until a release passes the audit |

## `backend/tests/`

| Path | Purpose |
|---|---|
| `conftest.py` | App/client fixtures; trains a small synthetic model once per session |
| `test_parser.py` | Three forwarding shapes; inline forward marks authentication missing |
| `test_features.py` | Feature count and order, phishing vs legitimate behaviour, behavioural thresholds |
| `test_reasons_and_bands.py` | Evidence-verified reasons, discard rules, fallback, band edges |
| `test_faithfulness.py` | The deletion test against a random control, and that a reformatted message keeps its band, score and reasons |
| `test_api.py` | Endpoints, upload limits, webhook secret/alias, history pollution, isolation |
| `test_auth_supabase.py` | JWT verification paths, 401 handling |
| `test_cors.py` | Configured origin allowed, unknown origin rejected, wildcard refused |
| `test_retention_and_cold_start.py` | Transactional delete, purge, neutral cold start |
| `test_evaluate.py` | Grouped-split evaluation harness on fixtures |
| `test_corpus_loading.py` | Extensionless hash-named corpus files and mbox-plus-loose-file loading |
| `test_download_datasets.py` | Archive fetch, checksum manifest, idempotent reruns, tar traversal rejection |
| `test_download_kaggle.py` | CSV-to-`.eml` conversion, hostile header values, manifest verification |
| `test_download_phishing_pot.py` | Date-header filtering, year thresholds, and phishing@pot shortcut masking tests |
| `test_evaluate_modern.py` | Leakage guard, dual-threshold metrics, domain-macro FPR, corpus-label collisions |
| `test_rls_contract.py` | Live-only PostgreSQL RLS contract (skips without credentials) |
| `test_email_verification.py` | The alias gate: unconfirmed 403, confirmed 200, unconfigured 503, and no alias row on refusal |
| `test_raw_storage.py` | Raw .eml storage in Supabase Storage with RLS and local filesystem fallback, object deletion and batch purge |

## `backend/data/sample_emails/`

Four demo messages used by the UI and the tests: PayPal phish, invoice phish forwarded inline, legitimate newsletter,
legitimate bank alert.

## `frontend/`

| Path | Purpose |
|---|---|
| `src/App.tsx` | Routes, `RequireAuth`, session provider wiring |
| `src/main.tsx` | Entry point; applies the stored theme before the first paint so there is no flash |
| `src/auth.tsx` | Supabase session context |
| `src/supabase.ts` | Client construction from `VITE_SUPABASE_*`, with this project's public URL and anon key as defaults |
| `src/api/client.ts` | `apiFetch`: base URL, bearer token, typed errors |
| `src/types.ts` | Response types shared across pages |
| `src/lib/cases.ts` | Search, filter, sort, pagination helpers (unit tested) |
| `src/hooks/useForwardingAlias.ts` | Alias endpoint result as a discriminated state: verified, unverified, unconfigured, error |
| `src/pages/Dashboard.tsx` | Upload, band counters, recent activity list |
| `src/pages/AnalysisDetail.tsx` | Band bar, verified reasons, SHAP table, features, delete |
| `src/pages/History.tsx` | Full record list with search, band filter, sort, pagination |
| `src/pages/Model.tsx` | Active model identity and metrics with the synthetic-data caveat |
| `src/pages/HowItWorks.tsx` | Pipeline and feature-group explanation |
| `src/pages/Status.tsx` | Health and model-loaded state |
| `src/pages/Profile.tsx` | Account identity, forwarding alias behind the verification gate, data-handling notice, trusted-sender baseline, sign out |
| `src/pages/Profile.test.tsx` | Verification gate states and the data-handling section |
| `src/pages/Login.tsx` | What the product is, the forwarding domain, and three ways in: email and password, Google, or a guest session |
| `src/pages/Login.test.tsx` | The forwarding panel, the Google button and the guest button |
| `src/components/Logo.tsx` | The brand mark: an inline SVG that inherits the text colour, so it themes |
| `public/` | The favicon as SVG and as 32/180/512 PNG rasters, plus `samples/` with demo `.eml` fixtures |
| `src/components/` | `AppShell`, `BandBar`, `ConfirmDialog`, `EvidencePanel`, `FeatureTable`, `ReasonCard`, `RiskBadge`, `SessionExpired`, `Toast`, `UploadBox` |
| `src/styles.css`, `src/styles/*.css` | Design tokens, shell, report, and status styles |
| `src/test/setup.ts` | Vitest setup (Testing Library matchers, jsdom cleanup) |
| `e2e/smoke.spec.ts` | Playwright smoke: unauthenticated check plus signed-in journey |
| `playwright.config.ts` | Chromium project, dev-server boot, `E2E_BASE_URL` support |
| `vite.config.ts` | Dev proxy to `:8000` (override with `VITE_DEV_API_TARGET`), Vitest config limited to `src/**` |
| `vercel.json` | Vercel build settings and SPA rewrite |
| `nginx.conf`, `Dockerfile` | Container build for the compose stack |
| `.env.example` | `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` |

## `supabase/migrations/`

| Path | Purpose |
|---|---|
| `0001_init.sql` | Tables, indexes, RLS enablement |
| `0002_auth_hardening.sql` | Idempotent policy hardening for the authenticated role |
| `0003_storage_raw_emails.sql` | Private storage bucket 'raw_emails' with 10 MB cap and tenant-isolated RLS policies on storage.objects |

## `docs/`

| Path | Purpose |
|---|---|
| `README.md` | Documentation index |
| `SUMMARY.md` | One-page project summary: what it is, how it decides, what is built, the numbers with caveats, what is not done, where to read more |
| `01`-`15` | Topic docs: overview, project log, plan, architecture, backend, frontend, data model, ML, explainability, API, security, deployment, testing, user study, risks |
| `16-demo-script.md` | Review walkthrough with expected screens and fallbacks |
| `17-real-corpus-evaluation.md` | Measured Nazario + SpamAssassin results, grouped split, caveats |
| `18-open-manual-actions.md` | Dashboard/account steps that still need the user, with values and verification |
| `20-model-parameters-and-features.md` | Canonical list of the 65 features, candidate hyperparameters, selection rule, calibration, bands and reason thresholds |
| `21-modern-corpus-evaluation-plan.md` | Modern-mail evaluation: measured 99.9% FPR on a modern inbox, the ablation that ruled out the obvious cause, the promotion gates, and the mailbox-training decision with its privacy constraint |
| `22-training-methodology-and-measurements.md` | The training method and every measurement it produced: the shortcut test, the temporal split, the operating points, the seed sweep, the confidence intervals, and the list of what is not tested |
| `23-cloudflare-email-forwarding.md` | Inbound email forwarding configuration: Cloudflare Email Routing, Worker integration, webhook contract, DNS verification |
| `decisions/ADR-001`-`014` | Decision records |
| `report/01`-`04` | Long-form report chapters |
| `report/final-report.md` | Submission write-up: objectives, implementation, verified results, limits |
| `report/2026-11-10-feature-expansion-report.md` | 57 → 65 feature expansion: new features, retrained metrics, ablation read, malformed-port fix, follow-ups |
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
| `scripts/send_sample.py` | Simulates a forwarded-email webhook |
| `scripts/purge_old.py` | Retention purge helper |
| `graphify-out/` | Code knowledge graph (regenerate with `graphify extract . --code-only`) |
