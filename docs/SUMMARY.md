# PhishLens in one page

Read this first. It is the whole project in about three minutes. Every claim here is expanded - and hedged where
the evidence is thin - in the numbered docs listed at the end.

## The idea

People are told "forward suspicious email to the security team", but the reply they get is usually a verdict with no
reason, or a wall of technical indicators that means nothing to them. PhishLens takes a forwarded email, scores it,
and answers in two parts: **how risky is it** (Low / Medium / High) and **why**, in plain language, with every reason
tied to something actually present in that email.

The design bet is that an explanation the user can check is worth more than a slightly more accurate black box.

## What a user does

1. Opens the web app and forwards the suspicious email as a file, or sends it to the webhook.
2. Gets a risk band, a 0-100 score, and a list of reasons ("the link text says example-bank.com but the link goes to
   example-bank.verify-login.top").
3. Sees the evidence behind each reason: the headers, links, or wording it was derived from.
4. Can revisit past cases in the cases list.

## How it decides, in one line per step

1. **Parse** the email: direct, forwarded inline, or forwarded as a `message/rfc822` attachment.
2. **Extract 65 features** in six groups: header authentication, URL, text/social-engineering, requested action,
   attachment metadata, and sender history.
3. **Score** with a calibrated tree model (XGBoost on the real corpus build), mapped to a 0-100 score and a band.
4. **Attribute** the score with SHAP, keeping the features that pushed hardest toward phishing.
5. **Write reasons** from those contributions, then **verify each one against the parsed email**. A reason that the
   email does not support is dropped; if nothing verifies, a generic reason is shown instead.
6. **Store** the analysis, the feature vector, and the explanations, and update sender history only for Low-risk mail.

## What is built

| Piece | State |
|---|---|
| Backend, FastAPI, 30+ endpoints | Working, 52 tests passing (1 live-only Supabase test skipped without credentials) |
| Feature extraction | 65 features across six groups, shared by training and serving |
| Model registry + calibration | Working; rejects feature-list mismatches |
| Reason engine | SHAP -> rules -> evidence check -> generic fallback |
| Web UI, React + TypeScript | Dashboard, analysis detail, cases, model info, status, settings; 18 unit tests plus a Playwright smoke suite |
| Auth and storage | Supabase auth (JWT verified in backend) and Postgres schema with RLS, applied to the live project |
| Deployment | Frontend on Vercel, backend on Render (free Docker tier), Supabase for auth/db |
| Real-corpus training and evaluation | Working and reproducible: fetch, dedupe, group-split, train, calibrate, evaluate |

## The numbers, with their caveats

- **65 features**, six groups. Adding a feature means retraining; serving and training share one ordered list.
- **Current model artifact** `xgboost-corpus-20261110-s7`, trained on **4,261 messages** after dedupe and after
  excluding 633 `spamassassin.taint.org` artefacts: 2,647 fit / 628 validation / 986 test, split by campaign or
  sender so no group appears on both sides.
- **Held-out test, calibrated**: F1 macro **0.978**, PR-AUC **0.986**, FPR **0.033**, Brier **0.014**.
  Uncalibrated it is 0.987 F1. One grouped split, no confidence interval.
- **The corpus on disk is now larger than the one the model saw.** On 2026-11-10 the fetcher was extended to every
  published Nazario year: 4,306 phishing + 2,712 legitimate = 7,018 messages after dedupe. The model above was not
  retrained on it, so the next training run will produce different (not comparable) numbers.
- **Do not read those numbers as field accuracy.** The corpora are 2003-2007 research mail (legitimate side) and
  2004-2025 phishing archives. The 2003 ham has no SPF/DKIM/DMARC headers, so "authentication headers missing" alone
  separates the classes almost perfectly. The honest conclusion: the pipeline works and the model ranks well on this
  data; real-world detection quality is unproven until it is measured on mail from this decade on both sides.

## The live demo is a pipeline demo, not the model above

The public deployment (Vercel + Render) runs a **synthetic-data model** baked into the Docker image, because the
real corpus model lives in a gitignored directory and is not promoted automatically. Live scores therefore prove
that forwarding, parsing, scoring, explaining, and storage all work end to end - they do **not** prove detection
quality. `GET /api/health` on the backend reports which model is active.

Known deployment facts: Render's free tier sleeps after 15 idle minutes, so the first request can take a minute; the
UI has no public sign-up, so an account must be created in the Supabase dashboard before signing in.

## What it does not do yet

- No real inbound-email provider (Gmail/IMAP): upload and webhook only. Forwarding as a mail rule is the stretch goal.
- No live domain-age lookup; age features are often "missing" and the model is trained to treat that honestly.
- No confidence interval on the corpus metrics, and no measurement on contemporary legitimate mail.
- No user study of whether the explanations actually help a non-expert. Protocol is written, not run.
- New features introduced in the latest expansion have no dedicated reason rule yet, so a verdict driven mainly by
  one of them falls back to the generic reason.

## Run it locally (Windows)

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m training.train --source synthetic --n 2400 --out models --reports reports
python -m uvicorn app.main:app --port 8000
```

Then, in a second terminal, `cd frontend; npm install; npm run dev`, open <http://localhost:5173>, and upload a file
from `backend/data/sample_emails/`. To train on real data instead, read
[19-teammate-training-guide.md](19-teammate-training-guide.md); it is the exact command list, including expected
output.

## Where to read more

| If you want | Read |
|---|---|
| the measured evaluation and its artefacts | [17-real-corpus-evaluation.md](17-real-corpus-evaluation.md) |
| all 65 features and the hyperparameters | [20-model-parameters-and-features.md](20-model-parameters-and-features.md) |
| what to click in a demo or viva | [16-demo-script.md](16-demo-script.md) |
| the submission write-up | [report/final-report.md](report/final-report.md) |
| the long story, in order | [02-project-log.md](02-project-log.md) |
| what is broken or unfinished | [15-risks-and-limitations.md](15-risks-and-limitations.md) |
| exact commands to train and ship | [19-teammate-training-guide.md](19-teammate-training-guide.md) |

Document index: [docs/README.md](README.md). Last updated 2026-11-10.
