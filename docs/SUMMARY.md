# PhishLens: one-page project brief

Read this first. It is the project in about three minutes. Every claim here is expanded, and hedged where the
evidence is thin, in the numbered docs at the end. Last updated 2026-11-11.

## What it is

People are told to forward suspicious email to a security team, but the reply is usually a verdict with no reason, or
a wall of indicators that means nothing to them. PhishLens takes the email, scores it, and answers two questions:
**how risky is it** (Low / Medium / High) and **why**, in plain language. Every reason is checked against something
actually present in that email before it is shown.

The design bet: an explanation the user can check is worth more than a slightly more accurate black box.

## What works today

| Piece | State |
|---|---|
| End-to-end pipeline | Parse -> 65 features -> calibrated XGBoost -> SHAP -> verified reasons -> store |
| Web UI (React + TypeScript) | Six screens: dashboard, history, analysis detail, model, profile, status; 20 unit tests and a Playwright smoke suite |
| Auth and storage | Supabase Auth (JWT verified in the backend) and Postgres with Row-Level Security |
| Deployment | Frontend on Vercel, backend on Render free tier, Supabase for auth and database |
| Training and evaluation | Public corpora -> dedupe -> grouped split -> train -> calibrate -> report; 86 backend tests pass (1 live-only Supabase test skips without credentials) |
| Model release gate | `audit_model.py` proves a model carries no personal data before it may be published |

## The number that matters, and the catch

- The released model `xgboost-corpus-20261111-s7` scores a held-out set of real mail: **FPR 0.022** at probability 0.5
  and **0.041** at the LOW/MEDIUM boundary on 2,865 legitimate messages from a modern inbox that it never trained on,
  and **recall 0.810** on 788 phishing messages from the 2024-2025 archives. Combined F1 0.806, ROC-AUC 0.961.
- **That is not field accuracy, and the caveats are measured.** It is fitted on one person's inbox and on a phishing
  corpus that is 20 years old. Its domain-macro false-positive rate (0.112) misses its 0.10 gate, its recall (0.810)
  misses its 0.90 gate, and its Brier score (0.039) misses its 0.02 gate. The gates and the trade are in
  [21](21-modern-corpus-evaluation-plan.md) section 14.
- Before the owner's mailbox was allowed into training, the corpora-only model flagged **99.9%** of legitimate modern
  mail. That history is kept in [21](21-modern-corpus-evaluation-plan.md) because the diagnosis is the point: modern
  legitimate mail has to be in the training set, and no feature mask can substitute for it.

## What we measured on modern mail (2026-11-11)

The corpora-only model, before the owner's mailbox was allowed into training, was scored against 2,216 received
messages from a real Gmail inbox (2020-2026) and against Nazario phishing it had never trained on:

| Measurement | Value |
|---|---|
| FPR on modern legitimate mail at probability 0.5 | **0.999** |
| FPR on modern legitimate mail at the LOW/MEDIUM boundary | **0.999** |
| Same, averaged per sender domain (domain-macro) | 0.996 |
| 95% CI (cluster bootstrap over 133 sender domains) | 0.997 - 1.000 |
| Bands on legitimate mail | 2,202 HIGH / 12 MEDIUM / 2 LOW |
| Recall on Nazario 2015-2023 (clean holdout) | 0.994 at the boundary |

The model catches modern phishing it has never seen and also calls essentially every modern legitimate message
phishing. Three separate hypotheses were tested and rejected as the cause:

- **Authentication-header leakage** (the original hypothesis): retraining without the 7 authentication features leaves
  FPR at 0.97; removing 9 era features does not help either.
- **Calibration**: the uncalibrated probabilities on the same messages already average 0.967, with 99.7% above 0.29.
- **Domain skew**: the domain-macro rate (0.996) is as bad as the message-level rate (0.999), so the failure is
  spread across senders, not caused by a few bulk senders.

The cause is the training data: the only legitimate mail in it is SpamAssassin 2003, so the classifier has never
seen a modern legitimate message and cannot represent one. Removing features cannot fix that; modern legitimate
mail has to be in the training set. No free public corpus of modern legitimate mail with real authentication headers
exists, so the corpora-trained model stays out of the live demo. The owner has now allowed the private mailbox to be
used for training, under a privacy constraint. Evidence and options:
[21](21-modern-corpus-evaluation-plan.md).

## The four-candidate protocol (2026-11-11)

With the mailbox approved as a training source, four candidates were trained on the same protocol and scored on one
shared holdout: 2,865 legitimate messages from 2026 that no candidate saw, and 788 phishing messages from the 2024
and 2025 archives.

| Candidate | Modern ham in training | FPR@0.5 | FPR@0.29 | Domain-macro | Recall@0.29 | Combined F1 |
|---|---|---:|---:|---:|---:|---:|
| A | one inbox, pre-2024 | 0.263 | 0.314 | 0.486 | 0.958 | 0.644 |
| B | A + 2003 ham | 0.071 | 0.179 | 0.386 | 0.900 | 0.770 |
| C | both inboxes, pre-2026 | 0.008 | 0.018 | 0.074 | 0.720 | 0.744 |
| D | C + 2003 ham | 0.022 | 0.041 | 0.112 | 0.810 | 0.806 |
| Gate | | <= 0.05 | <= 0.12 | <= 0.10 | >= 0.90 | - |

Putting real modern legitimate mail into training fixes the false-positive side by a factor of thirty: candidate C
flags 0.8% of legitimate mail where the corpus-only model flagged 99.9%. The cost is recall, because a model trained
on modern mail and old phishing learns that the notification mail that dominates a real inbox is normal.

**No candidate passes every gate.** Recall (0.90) and Brier (0.02) fail for all four. The best combined performer is D,
at FPR 0.022 and recall 0.810, which misses its domain-macro gate by 0.012 and its recall gate by 0.090. The full gate
table and the trade are in [21](21-modern-corpus-evaluation-plan.md) section 14.

## Data on disk

| Data | Messages | Dates | Role | Training use |
|---|---:|---|---|---|
| SpamAssassin ham | 2,712 | 2003 | legitimate | yes, but era-biased |
| Nazario phishing | 4,306 | 2004-2025 | phishing | yes |
| Google Takeout mailbox | 2,216 | 2020-2026 | modern legitimate training source and evaluation set | **yes**, by owner decision (2026-11-11); pre-2026 trains, 2026+ held out |

Totals after parsing and deduplication: 7,018 public messages, plus the private mailbox.

**What is missing:** a licence-clean modern ham corpus that can be shared. There is no free, registration-free public
one. The private mailbox is used for training by owner decision (2026-11-11), so the honest constraint is that a model
trained on it is personal-data-derived: no message content, address, subject or Message-ID may reach a committed
artifact, and the artifact must pass `backend/scripts/audit_model.py` before it may be published. The audit reads the
sender domains, addresses and distinctive subject words out of the mailbox and searches every file of the model
directory for them; a hit refuses the release.

## What is next

1. Improve recall without losing the false-positive fix. The released model misses 19% of held-out phishing at the
   triage boundary. The likely causes are the age of the phishing corpus and the loss of ham diversity, and both are
   addressable with more data rather than a feature change.
2. Fix the calibration. The isotonic calibrator is fitted on a split that mixes 2003 ham with modern ham, and the two
   have very different score distributions, so the Brier score (0.039) misses its 0.02 gate. Fitting on one era, or
   dropping the calibrator and thresholding the raw probability, would address it.
3. Replace the personal-mailbox training source with a licence-clean modern ham corpus when one exists, so the model
   stops being personal-data-derived and the privacy constraint disappears.

## What it does not do yet

- No live inbox integration (Gmail/IMAP): upload and webhook only.
- No live domain-age lookup; age features are often "missing".
- No user study of whether the explanations help a non-expert. The protocol is written, not run.
- New features from the latest expansion have no dedicated reason rule yet, so a verdict driven mainly by one of them
  falls back to the generic reason.

## Run it locally (Windows)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m training.train --source synthetic --n 2400 --out models --reports reports
python -m uvicorn app.main:app --port 8000
```

In a second terminal: `cd frontend; npm install; npm run dev`, open <http://localhost:5173>, and upload a file from
`backend/data/sample_emails/`. To train on the public corpora instead, follow
[19-teammate-training-guide.md](19-teammate-training-guide.md); it is the exact command list, including expected
output.

## Where to read more

| If you want | Read |
|---|---|
| the measured evaluation and its artefacts | [17-real-corpus-evaluation.md](17-real-corpus-evaluation.md) |
| all 65 features and the hyperparameters | [20-model-features-and-parameters.md](20-model-features-and-parameters.md) |
| what to click in a demo or viva | [16-demo-script.md](16-demo-script.md) |
| the submission write-up | [report/final-report.md](report/final-report.md) |
| the long story, in order | [02-project-log.md](02-project-log.md) |
| what is broken or unfinished | [15-risks-and-limitations.md](15-risks-and-limitations.md) |
| exact commands to train and ship | [19-teammate-training-guide.md](19-teammate-training-guide.md) |

Document index: [docs/README.md](README.md).
