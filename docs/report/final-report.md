# PhishLens - final report

**Explainable phishing triage by email forwarding**

BMSIT&M, Department of CSE - Mini Project (Batch 45), 2026-27 - Product Development category

| Member | USN |
|---|---|
| Md Saquib Ali | 1TE24CS174 |
| N Sai Yashwanth Simha | 1TE24CS178 |
| Nakshatra Chaudhary | 1TE24CS179 |
| Mourya M Goankar | 1BY24CS173 |

Guide: Dr. Shanthi D L

---

## 1. Abstract

Phishing warnings are either a binary verdict or a wall of indicators that a non-expert cannot act on. PhishLens
returns a risk level and the reasons for it, where each reason is a plain-language sentence backed by evidence
quoted from the email being analysed. The system parses a forwarded email, extracts 65 features in six groups,
scores it with a calibrated tree/linear model, converts SHAP contributions into candidate reasons, and discards any
reason whose evidence rule fails against the parsed message. The result is a Low / Medium / High band, a 0-100
score, and a short, verifiable explanation. PhishLens is implemented as a FastAPI service and a React interface,
with a PostgreSQL/Supabase schema, per-user data isolation, retention deletion, and a free-tier deployment path.

The engineering deliverable is complete and tested. The **detection model is a synthetic-data demo**, so this report
makes no claim about real-world phishing accuracy; the evaluation harness that produces that number is part of the
deliverable and is described in section 5.

## 2. Problem and objectives

A user who receives a suspicious email has three practical options: trust it, delete it, or forward it to an IT
desk that may reply hours later. Existing mail gateways answer a different question (is this message blocked?) than
the one the user has (should I act on this specific email, and why?).

Objectives:

1. Return a graded risk assessment per forwarded email, not just a boolean.
2. Explain the assessment in language a non-specialist can act on.
3. Ensure every stated reason is supported by the actual message, so an explanation can never assert evidence the
   email does not contain.
4. Keep the analysis auditable: store the feature values, the model identity, and the reason set for each case.
5. Ship a deployment that a student team can run and demo at zero cost.

## 3. What was built

### 3.1 Pipeline

```
forwarded email -> parser -> sender history -> 65-feature vector -> model + calibration
                -> probability -> score 0-100 -> band -> SHAP contributions -> candidate reasons
                -> evidence verification -> stored analysis + explanations
```

Eight design decisions carry the system:

- **One shared feature vector.** Training and serving import the same extractor, and the model registry rejects a
  model whose stored feature names or order disagree with the code. A silent train/serve skew is the most common
  way a demo model reports a number it cannot reproduce; this makes that failure loud.
- **Six feature groups.** Header (authentication results, display-name and domain mismatches, received-chain
  anomalies), URL (link count, IP-literal hosts, punycode, redirects, shorteners, host entropy), text (urgency and
  credential lexicons, structural cues), action (reply-to divergence, form and payment indicators), attachment
  (metadata only: names, double extensions, type claims), behavioural (deviation from the sender's trusted history).
- **Evidence-verified reasons.** A SHAP contribution nominates a feature; a template turns it into a sentence with
  the observed value; an evidence rule re-checks that value against the parsed email. If the rule fails, the reason
  is dropped. If a Medium or High result loses all reasons, a generic fallback is used rather than an unsupported
  claim. Inline forwards mark SPF/DKIM/DMARC as *missing*, not *failed*, because the headers genuinely were lost.
- **Conservative learning.** Sender history is updated only on Low-risk outcomes, so a hostile message cannot teach
  the profile that it is normal.
- **Attachments are metadata only.** Nothing is opened, rendered, or executed.
- **Per-user isolation.** Every query is scoped by `user_id`; the PostgreSQL schema adds Row-Level Security as
  defence in depth, and a live verification script checks isolation in both directions.
- **Retention as a feature.** Analyses are deleted transactionally with their explanations, and an admin-token
  guarded purge endpoint removes expired rows.
- **Honest surface.** The Model page shows the active model's identity and training metrics together with the
  synthetic-data caveat, so a reviewer cannot mistake a plumbing metric for a detection result.

### 3.2 Interfaces

| Surface | Content |
|---|---|
| Dashboard | Upload, band distribution, recent cases, summary counters |
| Analysis detail | Band bar and score, verified reasons with quoted evidence, SHAP contribution table, feature values by group |
| Cases | Search, band filter, sort, pagination, delete with confirmation |
| Model | Active model identity, feature count, metrics with the synthetic-data caveat |
| How it works | Pipeline stages and the six feature groups |
| Status | API health, model-loaded flag, last check |
| Settings | Forwarding alias, environment notices |
| Login | Supabase sign-in, or an explicit "authentication disabled" notice |

## 4. Verification (what is actually tested)

| Check | Command | Result |
|---|---|---|
| Backend suite | `cd backend; python -m pytest -q` | 44 passed, 1 skipped (live-only Supabase RLS test requires credentials) |
| Frontend unit tests | `cd frontend; npm test` | 18 passed in 5 files |
| Frontend E2E smoke | `cd frontend; npm run test:e2e` | 1 passed; the signed-in journey skips without `E2E_EMAIL`/`E2E_PASSWORD` |
| Production build | `cd frontend; npm run build` | Type-check and bundle pass (211 kB JS, 18 kB CSS before gzip) |
| API health | `GET /api/health` | `model_loaded: true` with the demo model installed |

The backend suite covers parser variants, all six feature groups, evidence-rule rejection, band thresholds,
API contracts, authentication and cross-user isolation, webhook secret and alias handling, retention deletion, and
the model endpoint. The reason-engine tests are the important ones for objective 3: they assert that a reason
without evidence is discarded, not merely down-weighted.

## 5. Data and evaluation status

Two evaluation paths exist in the repository:

- `backend/training/train.py --source synthetic` generates the bundled demo model. Its reported calibrated macro-F1
  (0.959) is measured on synthetic hold-out data and is **not** a phishing detection result.
- `backend/training/evaluate.py` is the real-data path: Nazario phishing plus SpamAssassin ham, grouped splits that
  keep a URL host and a sender domain inside one fold, cold-start measurement for senders with no history, and a
  random-split baseline for comparison. `backend/training/download_datasets.py` fetches the corpora and records
  SHA-256 manifests.

The real evaluation **has** been run. `python -m training.download_datasets` fetched 1,390 Nazario phishing
messages (819 campaign/host groups) and 2,712 SpamAssassin legitimate messages (468 sender-domain groups);
`python -m training.evaluate` then trained a throwaway XGBoost comparator on the production 65-feature matrix and
scored it on a campaign-and-sender-grouped split (3,092 train / 1,010 test):

| Metric | Grouped split (headline) | Random split (leaky baseline) |
|---|---|---|
| Precision | 0.968 | - |
| Recall | 0.930 | - |
| F1 | 0.948 | 0.962 |
| PR-AUC | 0.990 | 0.994 |
| FPR at threshold | 0.025 | - |

The 1.4-point grouped-vs-random gap is the evidence that the features carry signal beyond campaign and sender
identity. It is **not** evidence of production accuracy: labels are corpus-of-origin, the corpora are 2003-2007
traffic, there is one split with no confidence interval, and the comparator is not the shipped model. The shipped
model remains the synthetic demo model, and its 0.959 calibrated macro-F1 is still a synthetic hold-out number.
Method and caveats: `docs/17-real-corpus-evaluation.md`.

## 6. Security and privacy

| Concern | Handling |
|---|---|
| Authentication | Supabase JWT verification (HS256 or JWKS) behind `AUTH_MODE=supabase`; the disabled mode is explicitly local-only |
| Authorization | Owner-scoped queries plus RLS; verified by `backend/scripts/verify_rls.py` |
| Webhook abuse | Shared-secret header plus a 32-bit alias, with the secret required when enabled |
| Request size | Bounded chunked reads with a hard ceiling on both ingest endpoints, and a Content-Length pre-check |
| CORS | Explicit origin list; a wildcard is rejected at configuration time because Starlette would mirror the caller |
| Retention | Transactional deletion and an admin-guarded purge |
| Attachments | Metadata only, never opened |
| Secrets | Environment-only; no `.env` file is committed |

Known gaps: the 32-bit alias is brute-forceable in principle, development defaults must not be deployed unchanged,
and Docker Compose has not been executed in this environment.

## 7. Deployment

Target topology, all free tier: React frontend on Vercel, FastAPI container on Render's free Docker web service, and
Supabase for authentication and PostgreSQL. The repository contains `frontend/vercel.json`, `frontend/.env.example`,
`render.yaml` (the blueprint), and `backend/Dockerfile` with the synthetic demo model baked in at build time.
`docs/12-deployment.md` carries the exact settings, including the CORS origin list and the Supabase keys.

Verified: the Vercel deployment serves https://phishlens-gules.vercel.app, the Supabase project has both migrations and
all seven tables under RLS, and the local production build plus API round trip pass. Not verified yet: the Render build
and the end-to-end signed-in upload against the deployed backend, which need the service to exist first. Hugging Face
was evaluated and rejected as a host (HTTP 402: Docker Spaces are paid, free ZeroGPU Spaces need a 30-day-old account).

## 8. Limitations

1. Detection quality is measured only on 2003-2007 research corpora (grouped-split F1 0.948, single split, no
   confidence interval); the shipped model is the synthetic demo model, so nothing in the app's own output has been
   validated against real mail.
2. Behavioural features need history the system only sees for senders the user has already forwarded; cold start is
   neutral by design.
3. Inline forwarding loses the original authentication headers.
4. No real inbound provider; ingestion is file upload plus a simulated webhook. Gmail IMAP is designed in the spec
   and not implemented.
5. No domain-age or reputation lookup.
6. The frontend has no linter, and the dependency audit reports advisories whose fixes are major-version upgrades.
7. The synthetic demo model must not be presented as a detector in any external material.

## 9. Future work

1. Add bootstrap confidence intervals and a second seed to the real-corpus evaluation, plus a third-party holdout; one
   split cannot support a claim that two configurations differ.
2. Train the serving model on the real corpus (the documented `training.train --source corpus` path) once a holdout
   strategy beyond the two research corpora exists, so the app's own output stops being synthetic-pipeline demo.
3. Add Gmail IMAP ingestion so a user can forward without leaving their client.
4. Add domain-age and reputation enrichment behind the existing feature interface.
5. Run the user study in `docs/14-user-study.md` to test whether verified reasons change user decisions.
6. Add explanation-faithfulness measures (deletion test, stability across paraphrases) rather than only
   evidence-verification.

## 10. Reading path

- [Project log](02-project-log.md) - what was done, in order
- [Architecture](04-architecture.md), [backend design](05-backend-design.md), [frontend design](06-frontend-design.md)
- [ML pipeline](08-ml-pipeline.md), [explainability](09-explainability.md)
- [Testing and evaluation](13-testing-and-evaluation.md), [risks and limitations](15-risks-and-limitations.md)
- [Deployment](12-deployment.md), [demo script](16-demo-script.md)
- Decision records: `docs/decisions/`
