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
  API (upload, baseline, list/detail/features/delete, alias, model info, webhook), Supabase-JWT auth mode, tests (**30 passing**).
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

## 8. Low-impact hardening  - DONE
**Scope:** small changes that do not alter the feature set, model, thresholds, reason rules, or UI behaviour.
- Upload reads in 1 MB chunks and stops at 10 MB. The webhook streams its body, rejects an oversized declared
  `Content-Length` before reading, and allows the JSON envelope enough room for a 10 MB base64 payload.
- Raised the bundled nginx `client_max_body_size` from 12 MB to 15 MB so a near-limit JSON webhook is not rejected
  before the application sees it.
- Added regression tests for oversized upload and webhook requests. Suite: **30 passed**, one Starlette/httpx warning.
- Declared `requires-python = ">=3.11"` in `backend/pyproject.toml`.
- Clarified in `.env.example` and the README that its SQLite path is for Docker; local development uses `sqlite:///./phishlens.db`.
**Still open:** reverse-proxy body limits beyond the bundled nginx config, production auth/secret startup guard, alias entropy,
dependency-lock adoption, frontend major-version upgrades, Docker Compose and live Supabase verification.
