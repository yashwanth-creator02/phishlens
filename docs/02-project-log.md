# 02 - Project log: what was done, in order, and why

This is the complete record of the work done with Claude on PhishLens up to the creation of this repository (v0.1).
Dates are from the working sessions (Sep-Oct 2026). Status legend: **DONE**, **PARTIAL**, **NOT DONE**.

## 0. Starting point
Input: the written project definition (preserved in [original/original-project-idea.md](original/original-project-idea.md)) and
later the team's synopsis ([original/synopsis_mini_project_phishlens.docx](original/synopsis_mini_project_phishlens.docx)) and the
evaluation rubric screenshot (40 marks: literature survey and relevance; problem identification and objectives;
proposed methodology and expected outcomes).

## 1. Architecture design  - DONE
**Ask:** "a thorough architectural design" for the project definition.
**Done:** a modular-monolith design: ingestion -> parser -> six feature modules -> model -> SHAP -> explanation generator ->
risk scorer -> API; Supabase for DB/Auth/Storage; React frontend; Docker. Published as a Markdown document with Mermaid
diagrams (system context, sequence, ERD, deployment), repository structure, API table, ML lifecycle, security notes, phased roadmap.
**Key choices and why:**
- *One FastAPI service with internal module boundaries* instead of microservices - small team, easy to run, seams kept for later split (ADR-001).
- *Inbound-email webhook first, Gmail API later* - far less setup (no OAuth consent / Pub/Sub) (ADR-002).
- *Shared `features/` package for training and serving* - prevents train/serve skew (ADR-003).
- *Synchronous processing first, queue seam reserved* - simplest thing that works (ADR-004).
- *Templates, not an LLM, for explanations in v1* (ADR-005).
- *Open question flagged:* how to tie a forwarded email to an account -> per-user forwarding alias `u-<token>@domain`.
Output: the original architecture document (now split across `docs/04..13`).

## 2. Visualisations  - DONE
**Ask:** an image of the architecture, then "everything in a single pic".
**Done:** (a) a high-level 5-box flow, (b) a detailed single diagram: email client -> ingestion -> backend (parser, feature
extraction with the six modules, ML inference, SHAP, explanation generator, risk scorer, API) -> Supabase -> frontend.
Rendered as inline visuals in chat; the same content now exists as Mermaid sources and PNGs in [diagrams/](diagrams/).

## 3. Literature survey, problem identification, methodology (project report content)  - PARTIAL
**Ask:** create the literature survey, problem identification/objectives and methodology/expected outcomes per the rubric,
with the **latest references**, comprehensive, with diagrams, as one downloadable Word document.
**Research done (web):** current threat statistics (APWG Q2 2026, FBI IC3 2025), and 2023-2026 literature on explainable phishing
detection (SHAP/LIME), LLM-generated phishing, user studies of explanations/warnings, sender-behaviour detection.
**Verification discipline:** a claim was written only if it appeared in a source that was actually opened or in a verified
summary of it. Where only an abstract was read, the text and the comparison table say so ("not stated", "as stated in the
abstract"). Numbers taken from sources are listed in the report with the citation. Foundational references (SHAP, random
forests, XGBoost, RFCs, Enron corpus, lateral phishing) were cited from established knowledge.
**Notable verified sources:** Yi et al. 2026 (cross-dataset URL detection + SHAP); Uddin et al. 2025; Bhavana et al. 2025
(hybrid + LIME/SHAP); Heiding et al. 2026 (LLM spear phishing, N=101, 54% click-through, 97.25% LLM detection); Afane et al.
2024 (LLM-rephrased phishing evades filters); Wagner et al. 2025 (XAI nudge +10.1% accuracy); Roy et al. 2025 (PhishXplain, N=150);
Cau et al. 2025 (N=750, LLM vs expert explanations, hallucination risk).
**Existing references kept:** refs [1]-[5] of the synopsis stay as [1]-[5] so the synopsis and report can be merged.
**Content produced:** chapters 1 (introduction), 2 (literature survey: 11 sections, comparison table of 18 works, 6 research gaps G1-G6),
3 (problem identification, objectives with measurable criteria, scope, SDG), 4.1-4.9 (architecture, data flow, data, ingestion,
features, models, evaluation, explainability) - **now in [report/](report/) as Markdown**. 11 figures were rendered
(Mermaid via mermaid-cli + matplotlib).
**Not finished:** the **Word (.docx) build** was interrupted when the next request arrived. Still unwritten: sections 4.10-4.21
(risk scoring, API, data model, frontend, deployment, security, user study, testing, tools, plan, risks), chapter 5 (expected
outcomes) and 6 (conclusion) - their *content* now exists as design docs here (04-15) and is summarised in
[report/04-methodology-part-2-and-outcomes.md](report/04-methodology-part-2-and-outcomes.md). Assembling the final .docx (with
contents page and numbered figures/tables) is the remaining step.
**Findings worth knowing:** the synopsis already had refs [1]-[5]; I did not invent new ones; two tables/figure cross-references
in the first draft were off by one and were corrected.

## 4. Review-1 slide deck  - DONE
**Ask:** "Do surgical changes to this [FinGuard_Review1_final.pptx] according to my project."
**Method:** edited text runs in place (python-pptx), keeping every layout, table, flow box, logo and footer; replaced all FinGuard
(blockchain cross-border payments) content with PhishLens content slide by slide (title, intro, problem, objectives, 3 literature
tables with 12 papers, gap analysis, existing vs proposed system, two-phase methodology, module design, architecture diagram
labels, tools, SRS, outcomes, applications, SDGs, conclusion, 14 references). Verified by rendering every slide, schema validation,
and a search for leftover FinGuard terms.
**Fixed along the way:** slide 5 footer said "Review 0" / page 10 -> "Review 1" / 5; slide 1 had one line off by a paragraph index (caught in the render check);
file metadata ("last modified by" the other team's author) updated.
**Caveats:** footer date still 15/10/2026 (template value, review date unknown); a few gap-analysis cells say "Not stated/Not reported"
where only abstracts were available; outcome targets are labelled "to be validated".
Output: [presentation/PhishLens_Review1.pptx](presentation/) (+ `edit_deck.py`, the exact mapping script).

## 5. Repository v0.1 (this zip)  - DONE (with stated limits)
**Ask:** build the initial-version repo with docs containing every detail, including frontend, backend, etc.
**Built and tested here:**
- Backend: parser (direct / forward-as-attachment / inline forward), 6 feature modules (57 features), model registry,
  SHAP engine, 18 reason rules with evidence verification, risk bands, SQLAlchemy models, repository, analysis pipeline,
  API (upload, baseline, list/detail/features/delete, alias, model info, webhook), Supabase-JWT auth mode, tests (**28 passing**).
- Training: semi-synthetic generator (with confusable legitimate mail, LLM-style calm phishing, spoofed known senders, forwarding wrappers,
  histories), real-corpus loader, train/compare/select/calibrate/ablate script, auto-written training report.
- Frontend: Vite + React + TypeScript (builds cleanly), dashboard, detail, settings, login; screenshots captured from the live app.
- Ops: Dockerfiles, compose, env template, Makefile, CI workflow, Supabase SQL with RLS, helper scripts.
- Docs: this set.
**Bugs found by testing and fixed (useful lessons):**
1. *No-history shortcut:* the generator gave every legitimate email a sender history and almost no phishing one, so the model learned
   "no history => phishing" and scored everything as phishing in real use. Fixed: ~45% of legitimate mail is a first contact. (ADR-009)
2. *Domain-age skew:* domain age is unavailable at serving time (no WHOIS yet) but was present in training -> now available for only ~50% of training
   messages, and encoded with a "missing" flag.
3. *Plain-text legitimate mail* was out-of-distribution (training legit mail always had links) -> 30% of legitimate mail has no links.
4. *HIGH score with no reason* (no rule had evidence) -> a clearly generic fallback reason is shown instead of nothing or something invented.
5. *Reply-To semantics:* a known sender that never used Reply-To and suddenly does is now treated as a change.
6. *Poisoning guard:* sender history is updated only from known-good uploads or LOW-risk results, never from MEDIUM/HIGH. (ADR-007)
**Not done / not verified here:** real corpora (none downloaded), real inbound email provider integration, WHOIS/RDAP domain age,
Supabase live connection (SQLite used in tests), Docker build (no Docker in the build sandbox), the user study, the Word report assembly,
the browser add-on, LLM wording, async queue.

## 6. Decisions awaiting the team
See [03-plan-and-roadmap.md](03-plan-and-roadmap.md) section "Open decisions" - most important: which inbound email provider,
which corpora, how to obtain trusted sender history, hosting provider, and the review/submission dates.

## 7. Local run verification (Windows)  - DONE
**Environment:** Windows, Python 3.11.9 (the machine's default `python` is 3.10, which is too old for `datetime.UTC`),
Node 24.19.0, npm 11.17.0. No Docker available.

**What ran:**
- Frontend: `npm install` and `npm run build` completed; TypeScript reported no errors. `npm audit` reported 4 known
  advisories (3 moderate, 1 high) in Vite, esbuild, and React Router; fixes require semver-major upgrades.
- Backend: fresh `.venv`, `pip install -r requirements-dev.txt`, synthetic training with `--n 2400` selected
  `random_forest-synthetic-20261029-s7` (calibrated macro-F1 0.959 on the synthetic test split; not a real-world result).
- Tests: `28 passed` with one Starlette `TestClient`/`httpx` deprecation warning. The installed FastAPI/Starlette versions
  are newer than the pins in `requirements.lock.txt`, so the lock file should be refreshed before it is relied on.
- Runtime: `/api/health` reported `model_loaded: true`; the Vite dashboard, analysis detail, feature contributions,
  and settings pages rendered with no browser console errors. API uploads produced 98/HIGH for the PayPal phish
  (5 verified reasons), 7/LOW for the legitimate bank alert, and 98/HIGH for the inline-forwarded invoice phish
  (3 verified reasons).

**Not changed by this run:** Docker Compose, real-corpus training, Supabase auth, and the frontend audit findings remain
unverified or unresolved.

## 8. Run shortcuts
Added `backend.ps1` and `frontend.ps1` at the repository root so the app starts with `.\backend.ps1` and
`.\frontend.ps1` without changing directories. `backend.ps1` checks that `backend\.venv` uses Python 3.11 or newer
and exits with a clear message otherwise; a 3.10 venv fails on `websockets` and `datetime.UTC`.

## 9. Supabase RLS contract
Added the RLS/service-role distinction to `docs/11-security-privacy.md` and idempotent auth hardening in `supabase/migrations/0002_auth_hardening.sql`. `backend/tests/test_rls_contract.py` skips without live Supabase credentials; `backend/scripts/verify_rls.py` checks isolation in both directions when two user JWTs and two analysis IDs are supplied. The local suite still passes with one live-only skip.


## 10. Auth, deployment, and frontend foundation
Supabase JWT verification now supports HS256 or JWKS behind `AUTH_MODE=supabase`; disabled local mode is unchanged. Added `Dockerfile.space` and a GitHub Actions upload/health workflow for a free Hugging Face Space; Docker is not installed here, so the image build remains unverified. The frontend now has `apiFetch` with `VITE_API_BASE_URL`, a session provider, `RequireAuth`, and two Vitest tests. Backend suite is 37 passed plus one live-only RLS skip; frontend test and production build pass.

## 11. CORS hardening, browser smoke test, and submission docs
Closed out the deployment-facing work.

- **CORS.** `frontend/vercel.json` exists (Vite framework, SPA rewrite), and `backend/tests/test_cors.py` pins the
  contract: the configured origin is echoed, an unknown origin gets no CORS header, and `CORS_ORIGINS=*` is rejected at
  configuration time because Starlette would otherwise mirror the caller while credentials are allowed.
- **Browser smoke test.** Installed `@playwright/test`, added `frontend/playwright.config.ts` and
  `frontend/e2e/smoke.spec.ts`. The suite is split so it is useful in both modes: an unauthenticated check that passes
  locally, and a signed-in journey across dashboard, cases, model, how-it-works, status, settings, and case detail that
  skips unless `E2E_EMAIL`/`E2E_PASSWORD` are set. `E2E_BASE_URL` points it at a deployment. Vitest's `include` is now
  limited to `src/**` so the two runners cannot pick up each other's files.
- **Verified.** Backend 44 passed, 1 live-only skip. Frontend 18 Vitest tests in 5 files. Playwright 1 passed, 1 skipped.
  Production build type-checks and bundles. Chromium headless shell installed locally, so the smoke run needs no network.
- **Documentation.** Added `docs/report/final-report.md` (the submission write-up) and `docs/16-demo-script.md` (what to
  click during the review and what to say, with fallbacks). Updated this log, the docs index, `README.md` (test counts,
  frontend test commands), `docs/13-testing-and-evaluation.md` (frontend matrix and the real-data harness), and
  `AGENTS.md` (repository layout, verification checklist, known gaps).

**Still open, and honestly so:** the Vercel deployment, the Hugging Face Space build, and Supabase sign-in need account
credentials and were not exercised here. No production model has been trained on real mail; the shipped model is still
the synthetic demo.

## 2026-11-06 (later) - Real-corpus download, loader fix, and the first measured result

- **Fixed dead dataset sources.** `training/download_datasets.py` pointed at a 404 (`phish.tar.gz`) and at an HTML
  directory listing for SpamAssassin, so a run "succeeded" while acquiring only phishing mail. It now pulls three
  annual Nazario mboxes and two `old/publiccorpus` ham tarballs, is idempotent per source, records SHA-256 manifests,
  and extracts with `filter="data"` so a crafted archive cannot escape the target directory.
- **Fixed the silent class collapse.** `corpus.load_dir` and the manifest writer filtered on `.eml`/`.txt`, but
  SpamAssassin stores messages under numeric hashes with no extension: 2,712 legitimate files were on disk and 2 were
  loaded, which would have produced a phishing-only evaluation dressed up as a two-class one. Both modules now treat
  every non-archive, non-manifest file as a candidate and let the parser decide.
- **Fixed the working-directory assumption.** `training/evaluate.py` resolved dataset paths from the repo root, so the
  documented `cd backend` command raised "No emails found". Paths now resolve against the project root or the active
  directory.
- **Ran the evaluation.** 1,390 Nazario phishing (819 groups) and 2,712 SpamAssassin legitimate (468 groups);
  3,092 train / 1,010 test with campaign-URL-host and sender-domain groups kept whole. Grouped F1 0.948, precision
  0.968, recall 0.930, PR-AUC 0.990, FPR 0.025, confusion TP 422 / FP 14 / FN 32 / TN 542; random-split F1 0.962.
  The 1.4-point gap is the only argument here that the features work beyond campaign and sender identity, and one
  split with no confidence interval does not support more than that.
- **Verified.** Backend 47 passed, 1 live-only skip (`test_corpus_loading.py` and `test_download_datasets.py` added).
- **Documentation.** Added `docs/17-real-corpus-evaluation.md`; corrected the final report, the risk list, the testing
  page, the dataset card, `README.md`, `AGENTS.md` and `docs/FILE_INVENTORY.md`, all of which had said the real
  evaluation had never been run.
- **Right branch this time.** The work is on `feat/real-corpus-evaluation` (commit `4a861fb`), not on the UI branch.


## 2026-11-06 (deployment) - Branches merged, frontend live on Vercel, Supabase provisioned

- **Merged both lanes.** `feat/dashboard-ui` and `feat/real-corpus-evaluation` are on main via --no-ff merges
  (`03b0af8`, `2e052ab`) and pushed. The UI work, the mini-project pages, the corpus loader fix and the evaluation
  report are no longer branch-only.
- **Frontend deployed.** Vercel project phishlens (team yashwanth-creator02s-projects, Root Directory
  `frontend`) serves https://phishlens-gules.vercel.app. Vercel Authentication was disabled at the project level so
  the URL is public; VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set and baked into the bundle. Deploy with
  `vercel deploy --prod --yes` from the repository root, because the project root directory is `frontend`.
  Push-to-deploy is not connected: the Vercel GitHub App has no access to the private repo.
- **Supabase provisioned.** Project `vmbtdrmevlovvvfvtqmd` (phislens, eu-west-1, PostgreSQL 17) restored to
  ACTIVE_HEALTHY, then `0001_init.sql` and `0002_auth_hardening.sql` applied through the management API: 7 tables,
  RLS on all of them. Auth URL configuration and the email-confirmation toggle remain dashboard-only.
- **Verified.** Live URL returns 200 with the app HTML; a Playwright pass against the deployment shows the expected
  title, the "Analyst sign in" heading, three form controls, protected routes redirecting to sign-in, and no console
  errors. Local suites stay green: backend 47 passed / 1 skipped, frontend 18 passed, production build clean.
- **Still blocked on accounts.** The backend Space needs the Hugging Face account and HF_TOKEN/HF_SPACE_ID; the
  Vercel MCP token can create no projects (403); the Supabase MCP cannot read the database password.

- **Hugging Face ruled out; Render chosen (2026-11-06).** Two Space attempts returned HTTP 402: custom Docker Spaces
  need a paid plan, and free ZeroGPU Spaces need an account at least 30 days old. `Dockerfile.space`,
  `deploy/space/` and `.github/workflows/deploy-space.yml` are deleted. `render.yaml` defines a free Docker web
  service (`phishlens-api`) built from `backend/Dockerfile`, which now bakes the synthetic demo model at build time so
  the platform health check passes on cold start instead of waiting through a training run. Measured peak RSS for one
  upload-plus-SHAP analysis: 257 MB against Render's 512 MB free instance. `PHISHLENS_DATABASE_URL` accepts Supabase's
  bare `postgresql://` string because `app/db/session.py` rewrites it to `postgresql+psycopg://`
  (covered by `backend/tests/test_db_url.py`).

- **Render boot failed on the database password, fixed in code (2026-11-06).** The first Render deploy died inside
  `init_db()` with `psycopg.OperationalError: failed to resolve host 'h@i@s@h@_@aws-0-eu-west-1.pooler.supabase.com'`.
  The Supabase password contains `@`, and libpq splits userinfo at the last `@`, so the tail of the password became the
  host name. `app/db/session.py` now percent-encodes the password when the userinfo holds more than one `@`, and leaves
  an already-encoded password alone, so the dashboard copy-paste stays valid. Two regression tests added
  (`backend/tests/test_db_url.py`); suite 51 passed / 1 skipped. The Render MCP server is installed globally
  (`opencode mcp add render --global --url https://mcp.render.com/mcp`) and awaits OAuth sign-in.

- **Corpora-trained model measured, artefact diagnosed, teammate guide written (2026-11-06).** Added Nazario
  `phishing-2024` / `phishing-2025` (about 7,000 raw messages) to the fetcher, made downloads idempotent per source
  file, and excluded the `spamassassin.taint.org` sender-domain artefact (633 legitimate messages) from both
  `training/evaluate.py` and `training/train.py` so the report and the promoted model cover the same dataset.
  Grouped-split evaluation: precision 0.987, recall 0.987, F1 0.987, PR-AUC 0.998, FPR 0.012, confusion
  510/6/6/464 (3,275 train / 986 test). Promoted model `xgboost-corpus-20261106-s7` (xgboost, test F1 macro 0.983,
  FPR 0.027) lives only in gitignored `backend/models/active/`. Diagnosed why it scores both `legit_*.eml` demo
  samples at 1.0: `auth_missing` separates the corpora by 0.99 (2003 ham has no auth headers), `from_returnpath_mismatch`
  is inverted on mailing-list ham, and `http_only` is an era signal - documented in
  `docs/17-real-corpus-evaluation.md`, `docs/15-risks-and-limitations.md`, and the new
  `docs/19-teammate-training-guide.md`. Render still bakes the synthetic demo model; promoting this one is the
  open manual step in `docs/18-open-manual-actions.md`.

## 2026-11-10 - Feature expansion, retrained model, and parameter documentation

- **Feature set widened 57 -> 65 and the model retrained on it.** Eight offline features added across the existing
  groups: `max_path_depth`, `has_port`, `percent_encoding_ratio` (url), `subject_caps_ratio`, `generic_greeting`
  (text), `action_count` (action), `max_attachment_size` (attachment), `subject_reply_without_history`
  (behaviour). `training.train --source corpus` selected XGBoost again and wrote `xgboost-corpus-20261110-s7`
  (4,261 messages, 2,647/628/986 split, isotonic calibration): calibrated test precision 0.965, recall 0.989,
  F1 macro 0.978, FPR 0.033, ROC-AUC 0.993, PR-AUC 0.986, Brier 0.014. The earlier 57-feature run scored
  F1 macro 0.983 / PR-AUC 0.984, so this is not a controlled comparison; the per-group ablation in
  `docs/17-real-corpus-evaluation.md` shows header and url still carry the signal. The new
  `docs/20-model-parameters-and-features.md` is the canonical feature and hyperparameter reference.
- **Hardened URL parsing while adding `has_port`.** `urlparse(...).port` raises `ValueError` on a hostile href
  such as `https://example.com:99999/x`, which would have returned a 500 instead of a scored analysis. The
  extractor now treats an unparseable port as suspicious; `test_url_features_tolerate_malformed_port` covers it.
  Suite 52 passed / 1 skipped. No reason rule references the eight new features yet, so verdicts driven by them
  fall back to the generic reason - recorded as a follow-up in
  `docs/report/2026-11-10-feature-expansion-report.md`.

## 2026-11-10 - Full Nazario corpus fetch and a one-page project summary

- **Every published Nazario year is now fetched.** `download_datasets` pulls `phishing0`, `20051114`, `phishing1`,
  `phishing2`, `phishing3`, and `phishing-2015` … `phishing-2025` (15 files, 124 MB). Parsed and deduped: 4,306
  phishing messages, up from 2,182; with 2,712 SpamAssassin legitimate messages the corpus is 7,018 messages.
  The model was **not** retrained: `xgboost-corpus-20261110-s7` still reflects the 4,261-message fetch, and docs
  17/19 plus the dataset card now say so explicitly.
- **`docs/SUMMARY.md` added** as the three-minute read the other 20 docs cannot replace: the idea, the six pipeline
  steps, what is built, the numbers with their caveats, the demo-versus-real model distinction, what is not done,
  and a five-row reading guide. Linked from the root README and the docs index.

## 2026-11-11 - Modern-mail evaluation: the corpora model fails on real inbox mail

- **The corpora-trained model flags 99.9% of modern legitimate mail.** Scored against 2,216 received messages from a
  real Gmail inbox (2020-2026, 133 sender domains, 87% with links, 99.7% with SPF): FPR 0.999 at probability 0.5
  and at the LOW/MEDIUM boundary, 0.996 domain-macro, 95% CI 0.997-1.000, bands 2,202 HIGH / 12 MEDIUM / 2 LOW,
  mean probability 0.996. On the clean 2015-2023 holdout (2,072 phishing messages it never trained on) recall is
  0.994, so the model is neither blind nor weak on modern phishing; it is broken on modern legitimate mail.
- **Three candidate causes were tested and rejected.** Auth-feature leakage: retraining without the 7
  authentication features leaves FPR@0.29 at 0.971, and the 9-feature and header-group variants stay above 0.93.
  Calibration: the uncalibrated probabilities already average 0.967 with 99.7% above 0.29, so only 0.18% of
  messages cross the boundary because of calibration. Domain skew: the domain-macro rate (0.996) is as bad as the
  message-level rate (0.999). The real cause is the training data - the only legitimate mail in it is SpamAssassin
  2003, so the classifier has never seen a modern legitimate message. `docs/21-modern-corpus-evaluation-plan.md`
  section 7.1 holds the ablation table and the feature-level comparison.
- **The harness now enforces the temporal holdout rule.** `training.train` records the phishing date range and
  sources it trained on in `meta["training"]`; `training/evaluate_modern.py` refuses to report a window the model
  was trained on unless `--allow-training-overlap` is passed, defaults to the 2015-2024 window, and can score a
  candidate with `--model`. `training.train` gained `--phish-until` (drop phishing dated on or after the cutoff and
  undated phishing) and `--activate`, so an offline training run writes a candidate directory and never replaces
  `models/active`; the four call sites that need promotion (Dockerfile, entrypoint.sh, both Makefiles) pass it.
- **Consequence: the corpora model stays out of the live demo.** The synthetic demo model remains what Render
  serves. `docs/18-open-manual-actions.md` now carries the decision the owner has to make (allow a modern ham
  source for training, provide a licensed corpus, accept a synthetic-augmented model, or accept the honest
  limitation) and the privacy cleanup of the mailbox-derived cache. Docs 15, 17, 19, SUMMARY, README and AGENTS.md
  were updated to match. Suite: 68 passed, 1 skipped.

## 2026-11-11 - Owner decision: the mailbox may be used for training, with a privacy constraint

- **The decision.** The owner chose option A of the re-plan in `docs/21-modern-corpus-evaluation-plan.md` section 13:
  the personal Gmail Takeout mailbox may be used as a modern legitimate-mail training source. That is the only
  option that fixes the root cause, because the failure was never the features; it was that the training set contained
  no modern legitimate mail. The corpora-trained model is still not promoted as it stands, the synthetic demo model
  stays live on Render for now, and the auth-blind trade-off is rejected because the ablation gate failed rather
  than because a recall loss was judged acceptable.
- **The constraint is privacy, not permission.** No sensitive information or personal data may end up in committed
  artifacts or in the public deployment. Concretely: the trained model stays local (`backend/models/` is gitignored),
  it must not be baked into the Docker image or shipped to Render without a separate explicit decision, and reports
  and documentation may carry aggregate counts only, never message content, addresses, subjects or Message-IDs. The
  evaluation design that keeps the measurement honest is a temporal split on the mailbox itself: messages dated
  before 2024 may train the candidate, and 2024 and later are held out and never seen in training.
- **The derived cache is deleted; the raw export stays.** On the owner's instruction `.tmp/auth_cache` was deleted
  and the raw mbox export remains on disk. The aggregate numbers already written into the docs are unaffected, because
  no message content was ever recorded there. `docs/18-open-manual-actions.md` now lists only work that still needs the
  owner, and the decision rows in `docs/21-modern-corpus-evaluation-plan.md` section 10 record what was chosen.
