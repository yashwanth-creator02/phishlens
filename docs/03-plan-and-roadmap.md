# 03 - Plan and roadmap

## Strategy
Build a thin **end-to-end slice first** (done in v0.1) so integration problems surface early, then deepen each part.
Every increment ends in something demonstrable. Targets below are planned, not achieved.

## Increments

| Increment | Scope | State |
|---|---|---|
| **0 - Design** | architecture, repo layout, schema, diagrams, report content | DONE |
| **1 - MVP slice (v0.1)** | webhook/upload ingestion, parser, 6 feature groups, LR/RF/XGB training, SHAP + verified reasons, bands, API, web UI, tests | **DONE (this repo)** |
| **2 - Real data and honest evaluation** | assemble real corpora, re-train, E1-E8 experiments, error analysis, threshold selection, behavioural benchmark | TODO |
| **3 - Real ingestion and accounts** | pick provider + adapter, aliases for real users, Supabase Auth + Postgres + RLS live, retention job, domain-age provider | TODO |
| **4 - Evaluation with users** | user study (14-user-study.md), analysis, tune explanation wording | TODO |
| **5 - Stretch** | async queue (Redis+Celery), Gmail API path, browser add-on, counterfactual / LLM-worded explanations, multilingual | TODO |
| **6 - Submission** | final report (Word), slides, demo script, poster | partly drafted |

## Indicative 16-week plan (matches report Fig. 8)

| Weeks | Work | Output |
|---|---|---|
| 1-3 | literature survey, requirements | gap analysis (done in draft) |
| 2-5 | dataset collection and cleaning | corpora + dataset card |
| 4-7 | feature engineering | feature dictionary (v0.2 has 65) |
| 6-9 | model training and comparison | E1-E4 results |
| 8-11 | SHAP module and explanation templates | rules + audit of explanations |
| 7-11 | ingestion and backend API | real inbound email working |
| 9-13 | web interface | UI polish, history |
| 12-14 | integration and testing | E5-E8, error analysis |
| 13-15 | user study and analysis | study results |
| 14-16 | report and demo | final report, slides |
| 15-16 | browser add-on (optional) | prototype |

## Task checklist

Checked items are done and verified; unchecked items are genuinely open. The items that need the user are listed
in [18-open-manual-actions.md](18-open-manual-actions.md) rather than here.

**Data (Increment 2)**
- [x] Download Nazario phishing corpus and SpamAssassin public corpus (ham); record versions and licences
      (Enron is not used: it is 2001, and its era artefacts are worse than SpamAssassin's)
- [ ] Obtain LLM-rephrased / LLM-generated sets if licence permits (LLM-Nazario; Toth et al. 2025) for tests E4
- [x] Deduplicate; split by sender domain / campaign; keep a realistic imbalanced test set
- [x] Write a dataset card (sources, counts, label noise estimate, known biases) - [datasets/README.md](datasets/README.md)
- [ ] Build the semi-synthetic behavioural benchmark (Enron histories + injected spoof/compromise cases)

**Models (Increment 2)**
- [x] Re-implement one published pipeline as the "existing approach" baseline (URL-feature RF) - the
      `baseline_url_only_rf` row in every training report
- [x] Tune with grouped CV; calibrate; choose thresholds (the bands that ship are a product decision, and the
      report prints the validation-derived ones next to them)
- [ ] Run E1-E8 ([13-testing-and-evaluation.md](13-testing-and-evaluation.md)) completely; bootstrap CIs are done,
      McNemar is not
- [x] Feature pruning with SHAP + ablation; update the feature dictionary

**Explainability**
- [ ] Manual audit: 100 explanations, are they true, useful, and not misleading?
- [x] Faithfulness: deletion test and stability test - `backend/app/explain/faithfulness.py`, checked against the
      shipped model in `backend/tests/test_faithfulness.py`; the results are in
      [22](22-training-methodology-and-measurements.md) section 8
- [ ] Wording review with 3-5 non-technical readers

**System**
- [ ] Choose inbound provider (Postmark / Mailgun / SendGrid / Cloudflare Email Routing); write adapter in
      `backend/app/ingestion/`
- [ ] Domain-age provider (RDAP/WHOIS) with caching and timeouts, behind `DomainAgeProvider` - the seam exists and
      `NullDomainAge` is the default, so the feature is off
- [x] Supabase: apply `supabase/migrations/0001_init.sql`, connect backend with Postgres URL, test RLS
- [ ] Encrypt raw emails at rest (Supabase Storage or app-level); `scripts/purge_old.py` runs but is not scheduled
- [ ] Rate limiting on webhook and upload; the 10 MB request size limit is in place
- [x] Deploy (Docker on Render); CI already in `.github/workflows/ci.yml`

**User study (Increment 4)** - ethics/consent, materials, pilot, run, analyse ([14-user-study.md](14-user-study.md))

**Documents**
- [ ] Assemble the Word report from `docs/report/` (+ add sections 4.10-6, figures numbered, contents page)
- [ ] Update the Review-1 deck with real results when available

## Definition of done (per increment)
Tests pass in CI; docs updated; no number is reported unless it came from real data and a documented procedure; demo works from a clean checkout.

## Open decisions (need the team)
1. Inbound email provider and the bot domain (e.g. `phishlens.<domain>`).
2. Which corpora are allowed/available under the guide's rules; storage for large files.
3. How to obtain trusted sender history in real use: baseline uploads only (v0.1), or a mailbox connector later (see ADR-007).
4. Hosting provider and budget (free tiers vs one VM).
5. Review and final submission dates (the deck footer date is a placeholder).
6. Who owns which area (suggested split: data+models / backend+ingestion / frontend+user study / docs+evaluation).

## Immediate next steps (first two weeks)
1. Run the quick start; read docs 04, 08, 09. 2. Pick the provider and corpora (decisions 1-2). 3. Download corpora and run `training.train --source corpus`
once to see real numbers (expect lower than synthetic). 4. Start the dataset card. 5. Split work by owner.
