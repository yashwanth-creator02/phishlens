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

The six screens sit behind a fixed left sidebar with inline SVG icons, in a light or a dark theme that follows the
operating system until the user picks one. (The table above uses the names the screens had at the time of writing;
`Cases` is now `History` and `Settings` is now `Profile`.)

## 4. Verification (what is actually tested)

| Check | Command | Result |
|---|---|---|
| Backend suite | `cd backend; python -m pytest -q` | 115 passed, 1 skipped (live-only Supabase RLS test requires credentials) |
| Frontend unit tests | `cd frontend; npm test` | 23 passed in 6 files |
| Frontend E2E smoke | `cd frontend; npm run test:e2e` | 1 passed; the signed-in journey skips without `E2E_EMAIL`/`E2E_PASSWORD` |
| Production build | `cd frontend; npm run build` | Type-check and bundle pass (221 kB JS, 21 kB CSS before gzip) |
| Light/dark contrast | `python scripts/check_contrast.py` | Every checked foreground/background pair meets WCAG AA in both themes |
| API health | `GET /api/health` | `model_loaded: true` with the released model installed |

The backend suite covers parser variants, all six feature groups, evidence-rule rejection, band thresholds,
API contracts, authentication and cross-user isolation, webhook secret and alias handling, the email-verification
gate on the forwarding alias, retention deletion, and the model endpoint. The reason-engine tests are the important
ones for objective 3: they assert that a reason without evidence is discarded, not merely down-weighted.

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

### What the corpus model does on modern mail

The corpus-trained XGBoost model was scored against 2,216 received messages from a real Gmail inbox (2020-2026,
133 sender domains) with the same extractor the API uses:

| Measurement | Value |
|---|---|
| FPR at probability 0.5 | 0.999 |
| FPR at the LOW/MEDIUM boundary | 0.999 |
| FPR at the boundary, domain-macro | 0.996 (95% CI 0.997-1.000 pooled) |
| Bands on legitimate mail | 2,202 HIGH / 12 MEDIUM / 2 LOW |
| Recall on Nazario 2015-2023, a clean holdout | 0.994 at the boundary |

The model catches modern phishing it never saw and also calls essentially every modern legitimate message phishing.
Three candidate causes were measured and rejected: removing the seven authentication features leaves FPR at 0.971,
the uncalibrated probabilities already average 0.967 (so calibration is not moving the boundary), and the
domain-macro rate is as bad as the message-level rate (so it is not sender skew). The cause is the training data:
the only legitimate mail in the corpora is SpamAssassin 2003, which carries no authentication headers, so the
classifier has never seen a modern legitimate message. Feature removal cannot fix that; modern legitimate mail has
to be in the training set, and there is no free public corpus of it.

Consequences for this submission: adding modern legitimate mail to the training set is what makes the false-positive
side work, and it costs recall. The released model is a **trade**, not a clean win: it passes the false-positive and
domain-macro gates and misses the recall and the calibration gate. No accuracy claim is made for mail in general, and
none for another person's mailbox in particular. The contribution is the pipeline, the evidence-verified reason engine,
the security model and an honest evaluation that includes a measured failure with its root cause and a measured
source-leak with its own.

### The released model

Four candidates were trained against one shared 2026 holdout - 2,865 legitimate messages never seen in training and
788 phishing messages from the 2024-2025 archives - and the candidate the privacy audit cleared is the one that ships:

| Measurement (held-out 2026 split) | Value |
|---|---|
| FPR at probability 0.5 | 0.018 |
| FPR at the LOW/MEDIUM boundary | 0.021 |
| FPR at the boundary, domain-macro | 0.068 (gate: <= 0.10) |
| Phishing recall at the boundary | 0.770 (gate: >= 0.90, **missed**) |
| Combined F1 | 0.829 |
| ROC-AUC | 0.967 |
| Brier score | 0.026 (gate: <= 0.02, **missed**) |

The shipped model is `xgboost-corpus-20261112-s7`, an XGBoost over the same 65 features, fitted on the owner's
mailbox (before 2026-01-01), Nazario phishing before 2024, and the Kaggle CEAS 2008 and 419-scam corpora with
SpamAssassin ham. It passed `backend/scripts/audit_model.py` with zero findings: no sender domain, no email address
and no distinctive subject word from the mailbox is in the published artifact, and the SHAP background sample contains
no personal rows.

### What the feature set can and cannot see

The only modern legitimate mail in the training set is one inbox, so the features might identify the mail provider and
the era rather than the message being legitimate. That was measured, on legitimate mail only, across three corpora:

| Test | Accuracy | Chance |
|---|---|---|
| Classify the corpus of a legitimate email, all 65 features | **0.981** | 0.333 |
| The same, only the 13 header and format features | **0.980** | 0.333 |

The fingerprint is real and it lives in the headers: `received_hops`, `from_returnpath_mismatch`, `auth_missing` and
the SPF/DKIM/DMARC results. But the released model leans on those ten features for only **10.1%** of its gain; the
dominant signal is `subject_reply_without_history` at 41.5%. It is not simply recognising its own provider.

**The consequence for how these numbers may be quoted:** the 0.018 false-positive rate describes 2,865 held-out 2026
messages from the owner's own inbox. It is not a false-positive rate for email in general, and there is no second
modern legitimate corpus in this repository to measure that with. Method and reproduction:
`docs/21-modern-corpus-evaluation-plan.md` section 17.

## 6. Security and privacy

| Concern | Handling |
|---|---|
| Authentication | Supabase JWT verification (HS256 or JWKS) behind `AUTH_MODE=supabase`; the disabled mode is explicitly local-only |
| Authorization | Owner-scoped queries plus RLS; verified by `backend/scripts/verify_rls.py` |
| Forwarding alias | Issued only to an account whose email address is confirmed; the check reads the caller's own Supabase record and fails closed (503, never a silent pass) |
| Webhook abuse | Shared-secret header plus a 32-bit alias, with the secret required when enabled |
| Request size | Bounded chunked reads with a hard ceiling on both ingest endpoints, and a Content-Length pre-check |
| CORS | Explicit origin list; a wildcard is rejected at configuration time because Starlette would mirror the caller |
| Retention | Transactional deletion and an admin-guarded purge |
| Attachments | Metadata only, never opened |
| Secrets | Environment-only; no `.env` file is committed |
| Transparency | The Profile screen states what is stored, how long it is kept, and that forwarding an email processes the sender's personal data |

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

1. The released model is fitted on **one person's mail** and on a phishing corpus that is 20 years old. Its measured
   numbers (section 5) describe that combination: recall 0.770 against a 0.90 gate and Brier 0.026 against a 0.02
   gate are both missed, and nothing in the app's output has been validated against mail from an unrelated mailbox.
2. The feature set identifies the mail provider and the era, not only the message: legitimate mail from three corpora
   is classified by source with 0.981 accuracy, 0.980 on the header features alone. The released model leans on those
   features for 10.1% of its gain, so the effect is bounded, but the 0.018 false-positive rate is a statement about
   one inbox and not a general rate (section 5).
3. Behavioural features need history the system only sees for senders the user has already forwarded; cold start is
   neutral by design.
4. Inline forwarding loses the original authentication headers.
5. No real inbound provider; ingestion is file upload plus a simulated webhook. Gmail IMAP is designed in the spec
   and not implemented.
6. No domain-age or reputation lookup.
7. The frontend has no linter, and the dependency audit reports advisories whose fixes are major-version upgrades.
8. The synthetic demo model must not be presented as a detector in any external material, and neither may the corpus
   model's numbers be quoted without the caveats in section 5.

## 9. Future work

1. Add bootstrap confidence intervals and a second seed to the real-corpus evaluation, plus a third-party holdout; one
   split cannot support a claim that two configurations differ.
2. Train the serving model on real mail once a holdout strategy beyond the two research corpora exists, so the app's
   own output stops being a synthetic-pipeline demo. The `training.train --legit-mailbox` path and the temporal
   split in `docs/19-teammate-training-guide.md` step 6a are the mechanism; the constraint is that a model trained
   on a personal mailbox is personal-data-derived and stays out of the public deployment.
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
