# Train the PhishLens model on the real corpora - teammate walkthrough

This file is everything you need to go from a fresh clone to a corpora-trained model that the live service can serve.
No prior knowledge of PhishLens is assumed.

It is written for a teammate who has git, a terminal, and internet. Nothing in here needs AWS, Render, or the
Supabase dashboard. If you only want the demo model, use the commands in the root `README.md` instead.

## What you are doing and why

PhishLens scores suspicious emails with an ML model over 65 features extracted from six groups (header, URL, text,
action, attachment, behavioral). The result is turned into a Low / Medium / High risk band, and SHAP contributions
become plain-language reasons that are checked against evidence found in the email.

The repository ships with a model trained on **synthetic** (generated) emails. That model exists so the pipeline can
be run and demoed. It has never seen a real message, and its numbers are not evidence that phishing is detected. The
whole point of this walkthrough is to train on two real email corpora - Nazario (phishing) and SpamAssassin
(legitimate) - so the service can be described as measuring real mail, with honest caveats.

What you produce, in order:

1. `backend/data/raw/nazario/` and `backend/data/raw/spamassassin/` - the two corpora, downloaded and checksummed.
2. `backend/reports/evaluation.json` and `evaluation.md` - the grouped-split evaluation result. This is the number
   you may quote in a report, with its caveats.
3. `backend/models/<version_tag>/` and `backend/models/active/` - the trained, calibrated, registered model that
   the FastAPI service loads.
4. `backend/reports/training_report.json` - the training run record.

## Prerequisites

| Thing | Why | Minimum |
|---|---|---|
| Git | clone the repository | any recent version |
| Internet | install Python packages and download ~52 MB of corpora | - |
| Python | run the backend, the extractor, the training scripts | 3.11 or newer on Windows; `requirements.txt` targets 3.11+ and CI/Docker use 3.12. Python 3.10 will fail: the training code imports `datetime.UTC`. |
| Disk space | wheels for `scikit-learn`, `xgboost-cpu`, `shap`, the corpora, the model artefact | about 4 GB free |
| RAM | feature extraction runs over ~4,900 emails and trains in memory | 8 GB is comfortable; the run sized at roughly 1.5 GB peak |

Machine: Windows (PowerShell) is the documented path, thanks to the wrapper scripts. macOS/Linux work too - the
commands are identical except for the virtualenv activation line.

Check your Python before you start:

```powershell
python --version
python -m pip --version
```

On Windows the `python` on `PATH` is often an old system interpreter. If it prints 3.10 or lower, use the launcher
form for every Python command in this document:

```powershell
py -3.11 -m venv .venv
```

Node.js is not needed for this walkthrough. You can skip the frontend entirely.

## Step 1 - Clone the repository

```powershell
git clone https://github.com/yashwanth-creator02/phishlens.git
cd phishlens
git checkout main
```

Private repository. If the clone asks for credentials, sign in with your GitHub account or use `gh auth login`, and
make sure you are a collaborator. Clone over HTTPS or the SSH form you already use; either is fine.

## Step 2 - Create the virtual environment and install dependencies

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

What that installs (`requirements-dev.txt` includes `requirements.txt`):

- `fastapi`, `uvicorn[standard]`, `python-multipart`, `pydantic-settings` - the API.
- `sqlalchemy`, `PyJWT`, `cryptography` - database and Supabase auth verification.
- `beautifulsoup4`, `lxml`, `tldextract` - HTML parsing and public-suffix extraction for URL features.
- `numpy`, `joblib`, `scikit-learn`, `xgboost-cpu`, `shap` - the ML stack. `xgboost-cpu` is the CPU-only wheel of
  XGBoost; it imports as `xgboost` and avoids the multi-hundred-megabyte CUDA wheels.
- `pytest`, `httpx` - the test suite.

No PostgreSQL driver is needed for training; `psycopg` lives in `requirements-postgres.txt` and is only used when
the service talks to Supabase.

Verify the environment before training - this catches a wrong Python version in ten seconds:

```powershell
python -c "import sys, xgboost, sklearn, shap, joblib; print(sys.version)"
python -m pytest -q
```

Expected: `52 passed, 1 skipped`. The one skip is the live-only Supabase RLS test, which skips without credentials.
If pytest errors on import, your venv is built with the wrong interpreter - delete `.venv` and redo this step.

## Step 3 - Train the synthetic demo model (plumbing check, five minutes)

Do this first so a later failure is unambiguously yours to fix:

```powershell
python -m training.train --source synthetic --n 2400 --out models --reports reports
python -m uvicorn app.main:app --port 8000
```

Open http://localhost:8000/api/health and confirm `"model_loaded": true`. Stop the server with `Ctrl+C`.

What `training.train --source synthetic` does:

- Generates 2,400 emails (phishing-looking and legitimate-looking) deterministically with seed 7.
- Runs the production feature extractor over them, so training and serving share one feature code path.
- Trains three candidate models, picks one by comparison, fits an isotonic calibrator on a held-out slice, and
  registers the winner under `models/<version_tag>/`, copying it to `models/active/`.
- Writes `reports/training_report.md` and `training_report.json`.

`--n 2400` is arbitrary; the demo run upstream used it. The full comparison run used 3,092 training rows.

## Step 4 - Download the real corpora

```powershell
python -m training.download_datasets
```

Two things happen:

1. The fetcher downloads the corpora from their public mirrors into `backend/data/raw/<name>/`:
   - `nazario/`: every published file - `phishing0.mbox`, `20051114.mbox`, `phishing1.mbox`, `phishing2.mbox`,
     `phishing3.mbox`, and `phishing-2015` through `phishing-2025` (~124 MB total). Upstream stopped shipping a single
     tarball, so the fetcher pulls the per-year files; the set spans the 2003-2007 research mboxes and contemporary
     campaigns. `private-phishing4` is deliberately excluded because it contains donor-private messages, and
     `20051114.mbox` overlaps the 2005 mboxes; the loader dedupes on raw hash, Message-ID, and body hash.
   - `spamassassin/20030228_easy_ham.tar.bz2` and `20030228_hard_ham.tar.bz2` (~2.5 MB), extracted into
     hash-named files with no extension.
2. It writes `manifest.json` into each corpus directory: per-file SHA-256, total size and file count.

The step is idempotent, **per source file**. A source is downloaded only when neither the file nor an
already-extracted equivalent is present (an existing `phishing-2024.mbox` counts as covering the
`phishing-2024` source). Two useful variants:

```powershell
python -m training.download_datasets --dry-run        # print the plan, touch nothing
python -m training.download_datasets --names nazario  # one corpus only
```

What you should end up with after deduplication and parsing (see `docs/datasets/README.md`):

- `backend/data/raw/nazario/` - about 4,300 phishing messages in mbox files (measured 4,306 on 2026-11-10).
- `backend/data/raw/spamassassin/` - about 2,710 legitimate messages as extensionless hash-named files (measured
  2,712).

The committed evaluation and model figures were produced on a smaller fetch (the 2024/2025 archives only: 2,182
phishing, 4,261 messages total). With every year on disk the corpus is 7,018 messages, so both the split sizes and the
metrics below will differ; read the table as the expected shape, not the exact digits.

Two details that matter and that have bitten before:

- **Do not add an extension filter.** SpamAssassin ships files named like `0001.217ba49e4b19f7dad40f9526b1a2b1ba`,
  where the suffix is a content hash. The manifest writer and `corpus.load_dir` intentionally accept any
  non-archive, non-manifest file and let the parser decide. A `.eml`/`.txt` filter silently drops every legitimate
  sample and the run trains on phishing only. That behaviour was a real bug once; do not reintroduce it.
- Both corpora are gitignored. Nothing in `backend/data/raw/` is committed. Licences are public research corpora;
  do not redistribute them commercially or commit them.

## Step 5 - Run the evaluation (the number you may report)

```powershell
python -m training.evaluate --phish-dir data/raw/nazario --ham-dir data/raw/spamassassin --out reports
```

What `training.evaluate` does:

- Loads the corpora through the same parser and extractor used at serving time (65 features per email).
- **Excludes one corpus artefact before splitting**: SpamAssassin rewrites some hostnames to
  `spamassassin.taint.org`, which lands 633+ legitimate messages in a single sender-domain group that the grouped
  split puts entirely in one partition (about 40% of the test set belongs to one group). Both `training.evaluate`
  and `training.train` drop that one group and print how many messages they excluded, so the report and the promoted
  model always cover the same dataset. Everything else is untouched.
- Splits with `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)`. Phishing messages are grouped by
  campaign or first URL host; legitimate messages by sender domain. No campaign host and no sender domain appears in
  both train and test - about 3,275 train, 986 test (4,261 messages in total) on the corpus that produced the
  committed report; with every Nazario year downloaded the split scales with the corpus.
- Trains a throwaway comparator (`XGBClassifier`, `n_estimators=100, max_depth=4, learning_rate=0.1, random_state=7`)
  and measures it. **It never touches `backend/models/`.** The serving model is untouched by this step.
- Writes `backend/reports/evaluation.json` and `backend/reports/evaluation.md`.

Because a grouped split holds out whole groups by definition, every test sample is a cold-start sample; the report's
`cold_start_f1` equals the headline F1 on purpose. It also prints a random-split figure, which leaks campaign and
sender identity across the split. That number is a comparison baseline only - never quote it as the result.

### Expected output

On the 4,261-message corpus that produced the committed report, with these library versions, you should reproduce
something close to what is committed in `backend/reports/evaluation.json`:

| Metric | Grouped split (headline) |
|---|---|
| Precision | 0.987 |
| Recall | 0.987 |
| F1 | 0.987 |
| PR-AUC | 0.998 |
| False positive rate at the decision threshold | 0.012 |
| Train / test | 3,275 / 986 (4,261 messages total) |
| Confusion (TN / FP / FN / TP) | 510 / 6 / 6 / 464 |

The random-split F1 is 0.986 - there is essentially no gap between grouped and random splits on this corpus, which
is a sign that the model is not leaning on memorised campaign or sender identity.

Numbers will differ in the third or fourth decimal if a library version changed; a change in the first decimal means
something is wrong (most likely a corpus or artefact-handling change).

### What these numbers do and do not establish

Do establish: the extractor runs end-to-end on real mail and produces a usable feature matrix; performance holds
when whole campaigns and whole sender domains are withheld; recall is high enough that the explainability layer has
something worth explaining.

Do not establish: production accuracy. Labels follow the corpus of origin (Nazario is phishing-only by construction,
SpamAssassin ham is 2003-era mailing-list traffic), the data is old, there is no third-party holdout, and a single
split with a single seed has no error bar. The 4,261-message split is also skewed about 2:1 toward legitimate mail.

`evaluation` does **not** validate the shipped model - it validates the feature pipeline. If you do change the
feature set, thresholds, or reason rules, you must update the tests and the relevant `docs/` page in the same change,
and you must re-run the evaluation.

## Step 6 - Train the real model and promote it into `models/active`

```powershell
python -m training.train --source corpus `
    --phish-dir data/raw/nazario `
    --legit-dir data/raw/spamassassin `
    --phish-until 2024-01-01 `
    --out models --reports reports
```

Read step 6a before you promote anything.

What `training.train --source corpus` does:

- Loads both corpora with the same parser, and the same 65-feature extractor, in the same feature names and order as
  serving. The model registry rejects a model whose stored feature metadata does not match.
- With `--phish-until 2024-01-01`, drops every phishing message dated on or after the cutoff and every undated
  phishing message, so the 2024-2025 archives stay a clean holdout for the modern evaluation. Without the flag the
  whole corpus trains and those years become in-sample.
- Records what it trained on in `meta.json` under `training`: source directories, the cutoff, the phishing and
  legitimate date ranges, the number of dropped undated messages and the per-class counts. The modern evaluation
  reads that block and refuses to report a window the model was trained on.
- Applies the same `spamassassin.taint.org` exclusion as the evaluation, so the promoted model covers the same
  dataset the report describes, then splits by group with the same settings (fit/validation/test =
  2,647 / 628 / 986).
- Trains three candidates on the training rows:
  - Logistic regression (`max_iter=2000, C=1.0, class_weight="balanced"`).
  - Random forest (`n_estimators=300, max_depth=12, min_samples_leaf=2, class_weight="balanced", n_jobs=-1`).
  - XGBoost (`n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9`,
    `scale_pos_weight` set from the class ratio).
- Selects the candidate with the highest F1 subject to a **false-positive-rate ceiling of 0.03**. A model above the
  ceiling is not promoted, however high its F1.
- Fits an **isotonic calibrator** on a held-out slice of the training data so probabilities are comparable across
  runs, and a minimum-importance threshold per model family so only features that actually matter appear in the
  explanation (`REASON_MIN`: xgboost 0.10, logistic regression 0.10, random forest 0.02).
- Writes `backend/models/<version_tag>/` (`model.joblib`, `calibrator.joblib`, `meta.json`, `background.npy`) and
  `backend/reports/training_report.json` and `training_report.md`.

**It does not touch `backend/models/active/` unless you pass `--activate`.** That is deliberate: an offline
training run must never replace the serving model. The command above writes a candidate directory. When you have
evaluated the candidate and want to serve it, add `--activate` (or copy the tag directory over `models/active/`).

A useful flag for a quick sanity run before the full one: `--limit 500` caps emails per class. Do not use it for the
model you promote.

### Expected output

- Console: `dataset: N emails, ...` then the `Excluding 633 messages ...` line, then the selected model and the
  registered version tag (for example `xgboost-corpus-20261106-s7`, date and seed vary).
- `backend/models/active/` contains `model.joblib`, `calibrator.joblib`, `meta.json`, `background.npy`.
- `backend/reports/training_report.md` lists the candidates, the cut, and the calibration quality (Brier score).
- The last full run selected **xgboost** with held-out test metrics after calibration: precision 0.971,
  recall 0.994, F1 macro 0.983, FPR 0.027, ROC-AUC 0.992, PR-AUC 0.984, Brier 0.014
  (confusion TN/FP/FN/TP = 502/14/3/467).
- Test metrics should be in the same neighbourhood as the evaluation comparator in `docs/17-real-corpus-evaluation.md`;
  they are not expected to match exactly, because the promoted model is a different selected candidate on a different
  internal slice. If F1 is far below 0.9 or the false-positive rate is above 0.05, stop - something is wrong.

## Step 6a - Measure the candidate on modern mail before you promote it

This step exists because the corpora-trained model has a measured limitation: scored against 2,216 received messages
from a real Gmail inbox (2020-2026), it flags **99.9%** of them as phishing. The cause is the training data, not the
classifier: the only legitimate mail in the corpora is SpamAssassin 2003, which has no authentication headers at
all, so "authenticated mail" reads as "phishing". Removing the authentication features does not fix it. Full
evidence in [21](21-modern-corpus-evaluation-plan.md) section 7.1.

If you have a modern legitimate-mail source (a licensed export, a shared research corpus), score the candidate
against it before promoting:

```powershell
python -m training.evaluate_modern `
    --model models/<version_tag> `
    --phish-dir data/raw/nazario `
    --phish-since 2015-01-01 --phish-until 2024-01-01 `
    --out reports/modern
```

`--model` points at the candidate directory, so a candidate is scored before it replaces anything. The harness
refuses to run when the model was trained on phishing from the requested window, because that would report
in-sample recall as if it were generalization.

The promotion gates are the ones in [21](21-modern-corpus-evaluation-plan.md) section 9: FPR at probability 0.5
at most 0.05, FPR at the LOW/MEDIUM boundary at most 0.12, domain-macro FPR at most 0.10, held-out 2015-2023 recall
at least 0.90, historical grouped macro-F1 at least 0.95, Brier at most 0.02. A partial pass is a fail. If you
cannot reach those gates because no modern ham corpus exists in your environment, say so in the write-up instead of
promoting: "measured FPR 0.999 on modern inbox mail, root cause identified, remedy needs data we do not have" is a
defensible result, and a model that cries wolf on every legitimate mail is not.

## Step 7 - Verify the newly trained model locally

```powershell
python -m pytest -q
python -m uvicorn app.main:app --port 8000
```

Confirm http://localhost:8000/api/health returns `"model_loaded": true` and the model field names your new version
tag. Then upload one sample from `backend/data/sample_emails/`:

```powershell
curl.exe -X POST http://localhost:8000/api/analyses/upload `
  -F "file=@backend/data/sample_emails/phish_paypal_direct.eml"
```

You should get a scored analysis with a band and at least one verified reason. `curl.exe` is the Windows build of
curl; plain `curl` in PowerShell is an alias for `Invoke-WebRequest` and will fail on `-F`. Stop the server with
`Ctrl+C`.

## Step 8 - Ingesting modern mailbox data (avoiding era artifacts)

Because SpamAssassin 2003 ham lacks modern authentication headers (`Authentication-Results`, SPF/DKIM/DMARC) and uses old URL conventions (`http://`), models trained purely on 2003 data can misclassify modern legitimate email. To train on modern data from your own inbox:

1. Export your Gmail mailbox via Google Takeout (`All mail Including Spam and Trash.mbox`).
2. Place the `.mbox` file into `backend/data/raw/mailbox/` (this path is gitignored).
3. The corpus loader provides `corpus.load_mailbox()`, which automatically parses personal mbox exports and skips messages labeled as Spam or Trash (`X-Gmail-Labels`).
4. You can combine modern mailbox ham with Nazario phishing to evaluate and train against contemporary email patterns without era skew.

### Known artefact - read before you are surprised

The promoted model will score both `legit_*.eml` samples in `backend/data/sample_emails/` at the ceiling (raw
probabilities 0.997 and 0.999, calibrated to 1.0). That is a **data artefact, not a model bug**, and it is also true
of a large slice of the legitimate corpus. Measured origin of the problem, over 800 messages per class:

- **SpamAssassin's 2003 ham has no `Authentication-Results` headers at all.** The parser marks all three checks
  `missing`, so `auth_missing = 1.0` for roughly 100% of the legitimate class (Nazario phishing: 1.1%). Meanwhile
  `spf_pass`, `dkim_pass`, `dmarc_pass` are 0.0 for ham and 0.78 / 0.72 / 0.60 for phishing. This one feature
  separates the classes by 0.99 - more than any genuine signal - and the model learns "headers present and
  passing" as a phishing signal, which is backwards from what a modern reader expects.
- **Return-path mismatch is inverted on this corpus**: 84% of ham carry a `Return-Path` on a different domain than
  `From` (mailing-list bounces), versus 13% of phishing. Modern legitimate mail (a newsletter with return-path and
  From on the same domain, like `legit_newsletter.eml`) gets `from_returnpath_mismatch = 0`, the phishing side of
  this feature as well.
- `http_only` URL share is 67% for ham and 13% for phishing - another era signal (2003 mail used `http://`
  everywhere), not a phishing signal.

A modern legitimate email that carries full SPF/DKIM/DMARC pass headers (which is exactly what
`legit_newsletter.eml` and `legit_bank_alert.eml` are) lands in the region the model associates with phishing on
all three counts, and scores near 1.0. The genuinely phishing-side signal that remains (`requests_click` at
0.45 vs 0.003, header/auth failures) is real but much smaller than the artefacts.

Practical consequences for the demo and for describing the results:

- **Do not demo the corpora-trained model with the two `legit_*.eml` samples.** Use `phish_paypal_direct.eml` and
  `phish_invoice_forwarded_inline.eml` (both HIGH, as expected), and say plainly that the legitimate demo samples
  carry modern authentication headers that this corpus-era ham never had.
- The synthetic demo model does not have this problem, because the generator emits the same header distribution for
  both classes. That is one reason the Docker image still bakes the synthetic model (step 8).
- Anyone quoting the evaluation numbers should know they are measured on a corpus where header pass/missing is a
  near-perfect separator. This is the single largest caveat on the result; it belongs in any report or viva answer
  alongside the F1. See `docs/15-risks-and-limitations.md`.

If a future dataset supplies legitimate mail with real `Authentication-Results` headers (for example a modern
ham corpus), retraining on it is the correct remedy - not tuning the thresholds to make the demo samples score low.

## Step 8 - Ship it to the live service

`backend/models/` and `backend/data/raw/` are gitignored, so a trained model does not reach Render by itself. Today
the Render image (`backend/Dockerfile`) bakes in the **synthetic demo model** at build time so the health check
passes on a cold start, and `render.yaml` sets `PHISHLENS_AUTO_TRAIN_DEMO=true`. The first supported way to ship the
corpora-trained model is the two-step change below; do it in one commit so the image and the flag never disagree:

1. In `backend/Dockerfile`, replace the bake-in line with a copy of the promoted model, and delete the training
   invocation:

   ```dockerfile
   COPY models ./models
   ```

   and remove `RUN python -m training.train --source synthetic ...`. The build context is `./backend`
   (`dockerContext: ./backend` in `render.yaml`), so the promoted artefact at `backend/models/active/` lands at
   `/app/models/active` in the image, where the registry loads it.

2. In `render.yaml`, set the flag to `false`:

   ```yaml
   - key: PHISHLENS_AUTO_TRAIN_DEMO
     value: "false"
   ```

3. Commit the artefact (the `git add -f` is required because `backend/models/` is ignored):

   ```powershell
   git add -f backend/models
   git commit -m "chore: promote corpus-trained model into the image"
   git push
   ```

Render auto-deploys on `main`. The model artefact plus the Docker image layers fit the free 512 MB instance: the
demo run peaked at about 257 MB RSS for one analysis, and the promoted artefact is about 405 KB on disk
(`model.joblib` 363 KB, `background.npy` 45 KB, plus two small files).

Whichever way you ship it, verify the live service afterwards:

```powershell
curl.exe https://phishlens-api-6esn.onrender.com/api/health
```

The `model` field must name your promoted model, and `auth_mode` must read `supabase`. Remember the free instance
sleeps after 15 idle minutes, so the first request takes about a minute.

Note the artefact above before shipping: shipping the corpora-trained model changes what the live demo reports for
legitimate-looking mail (step 7). Decide as a team whether the honest caveat is acceptable for the demo, or whether
the demo stays on the synthetic model and the corpora run stays as the measured evidence.

## Rules you must not break

- **Evaluation never overwrites the serving model.** `training.evaluate` trains a comparator in memory and discards
  it. If you add a flag to write it into `backend/models/active`, that is a deliberate, reviewed change, not a tidy-up.
- **Training and serving share the feature names and order.** The registry rejects a mismatched `meta.json`. If you
  change the extractor, retrain and update the tests and the docs page in the same change.
- **The artefact exclusion must stay in both scripts.** If `training.train` and `training.evaluate` stop covering
  the same dataset, their numbers silently stop being comparable.
- **Never commit the corpora, a `.env`, `.venv/`, `reports/`, or a `.db` file.** `backend/.gitignore` covers them;
  `git add -f` on `backend/models/` is the only sanctioned exception, and only for a model you are promoting.
- **Attachments are metadata only.** Never open, execute, or render them.
- **Inline forwarding loses the original SPF/DKIM/DMARC headers**; they are treated as missing, never as failed.
- **Quoting numbers**: the synthetic model's metrics are a plumbing check. The evaluation numbers are measured on
  2003-2007 corpora (with 2024-2025 phishing added) with one grouped split and no confidence interval, and on a
  corpus where authentication-header presence separates the classes. Neither is a production-accuracy claim.

## If something goes wrong

| Symptom | Likely cause | Fix |
|---|---|---|
| `ValueError: No emails found under ...` | The corpus directories do not exist, or the flags point at the wrong relative paths | Run `python -m training.download_datasets` from `backend/`; pass `--phish-dir data/raw/nazario --ham-dir data/raw/spamassassin` |
| Download returns 404 or empty corpora | Upstream mirror change; the URLs live in `DATASETS` in `backend/training/download_datasets.py` | Update the URL there, or drop the files into `backend/data/raw/<name>/` yourself and rerun; the fetcher skips sources already on disk |
| `ImportError: cannot import name 'Self'` / `datetime.UTC` | Virtualenv built with Python 3.10 | Delete `.venv`, recreate with `py -3.11 -m venv .venv` |
| `psycopg.OperationalError: failed to resolve host '...@aws-0-...'` | The database password contains `@` and the URL was not encoded; `app/db/session.py` handles `@` automatically but `#`, `?`, `/` must be percent-encoded by hand | Percent-encode those characters in the connection string |
| `health` shows `model_loaded: false` | No model in `backend/models/active/`, or the registry rejected the feature metadata | Retrain so `backend/models/active/meta.json` matches the extractor; confirm the 65 feature names and order |
| Test suite fails after retraining | The training run changed `meta.json` in a way the tests do not expect | Read the failing test; do not lower a threshold to make it pass |
| Legitimate sample emails score HIGH | The `auth_missing` corpus artefact (step 7) | Expected with the corpora-trained model; use the phish samples for the demo, or stay on the synthetic model |
| Render deploy fails, or health never turns green | The image still trains the demo model and the promoted artefact is not in the image | Follow step 8: copy the model in the Dockerfile and set `PHISHLENS_AUTO_TRAIN_DEMO=false` in `render.yaml` |

## Further reading

- `docs/17-real-corpus-evaluation.md` - the evaluation result, what it establishes, and what it does not.
- `docs/datasets/README.md` - corpus provenance, licences, and the split rule.
- `docs/08-ml-pipeline.md` - the feature set, the behavioural benchmark, and the evaluation plan.
- `docs/15-risks-and-limitations.md` - honest limits, including the corpus age and header-artefact problems.
- `docs/12-deployment.md` - how the live deployment is configured.
- `docs/18-open-manual-actions.md` - the one remaining decision, with exact steps.
- `AGENTS.md` - the working rules for this repository, including the invariants above.
