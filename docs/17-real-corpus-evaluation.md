# Real-Corpus Evaluation (measured)

This page reports what the pipeline actually scores on real phishing and legitimate mail, and what that number
does and does not prove. Everything here was produced by committed code; the corpora themselves are gitignored.

## What was run

```powershell
cd backend
python -m training.download_datasets
python -m training.evaluate --phish-dir data/raw/nazario --ham-dir data/raw/spamassassin --out reports
```

Raw artifacts: `backend/reports/evaluation.json` and `backend/reports/evaluation.md` (generated, untracked).
Corpus provenance and download details: [docs/datasets/README.md](datasets/README.md).

## Corpus

| Class | Messages loaded | Split groups | Grouping key |
|---|---|---|---|
| Phishing (Nazario) | 2,182 | 1,233 | campaign / first URL host |
| Legitimate (SpamAssassin) | 2,712 | 468 | sender domain |
| Total loaded | 4,894 | 1,701 | |

633 legitimate messages whose sender domain is `spamassassin.taint.org` are excluded before splitting (see
"Artefacts" below), so the evaluated dataset is 4,261 messages.

Dated note (2026-11-10): the fetcher now downloads every published Nazario year, which yields **4,306 phishing
messages** and **7,018 messages in total** after dedupe. The table and every metric below describe the earlier,
smaller fetch that the promoted model and the committed report were built from. They have not been recomputed on the
expanded corpus; doing so changes the split sizes and, because the extra years are older campaigns, probably the
feature distributions too.

The corpus is skewed toward legitimate mail (2:1). Labels follow the corpus of origin, which is the usual
labelling shortcut and the main reason these numbers cannot be read as production accuracy: Nazario is
phishing-only by construction and SpamAssassin ham is 2003-era mailing-list traffic, so "legitimate" here means
"not in a phishing corpus", not "a benign modern business email".

Both corpora are old. SpamAssassin ham is dated 2003. The Nazario mbox files cover roughly 2003-2007 and, in the
expanded fetch, 2015-2025, which brings contemporary campaigns into the phishing set. Header
habits, URL shorteners, HTML-only bodies, tracking pixels, and attachment patterns of 2020s mail are
underrepresented, so the score measures the pipeline's feature extraction and the corpus separation, not today's
attacker-vs-defender gap.

## Artefacts

Two corpus artefacts shape these numbers. Both are handled in code, and both are flagged here because a reader who
only sees the F1 will over-read it.

1. **`spamassassin.taint.org` (excluded).** SpamAssassin rewrites some hostnames to `spamassassin.taint.org`, which
   lands 633 legitimate messages in one sender-domain group. That single group was about 40% of the test set and
   85% of the false positives when kept, purely because the grouped split put it entirely in one partition.
   `training/evaluate.py` and `training/train.py` exclude that one group and print the excluded count, so the
   report and any promoted model cover the same dataset. The remaining 2,079 legitimate messages are untouched.
2. **`auth_missing` separates the classes (not excluded, but load-bearing).** SpamAssassin's 2003-era ham has no
   `Authentication-Results` headers, so `auth_missing = 1.0` for essentially all legitimate messages. Nazario
   phishing usually does carry them, so `spf_pass` / `dkim_pass` / `dmarc_pass` are often 1.0 for phishing. The
   model therefore learns "headers present and passing" as a phishing signal, which is the opposite of what a
   modern reader expects. A modern legitimate email with full SPF/DKIM/DMARC pass lands in the phishing region and
   is scored near 1.0. This is the single largest caveat on the result. The full walkthrough, with the demo
   implications, is in `docs/19-teammate-training-guide.md` step 7.

## Split

Primary result uses `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)` with groups as above: no
campaign host and no sender domain appears in both train and test. 3,275 train / 986 test.

Because a grouped split holds out whole groups by definition, every test sample is a cold-start sample: the report's
`cold_start_f1` is therefore identical to the headline F1, and its `cold_start_n` equals the test size. That is
expected arithmetic, not two independent findings.

A random stratified split on the same rows is reported only as the comparison baseline. It leaks campaign and
sender identity across the split and is not a result.

## Model under evaluation

`training/evaluate.py` trains a throwaway `XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
random_state=7)` on the 65-feature matrix produced by the production extractor, then discards it. The serving model
in `backend/models/` is untouched, and none of these numbers describe it.

## Results

| Metric | Grouped split (headline) | Random split (leaky baseline) |
|---|---|---|
| Precision | 0.987 | - |
| Recall | 0.987 | - |
| F1 | 0.987 | 0.986 |
| PR-AUC | 0.998 | 0.999 |
| FPR at decision threshold | 0.012 | - |

Confusion counts behind grouped F1: 986 test samples, TP 464 / FP 6 / FN 6 / TN 510 (470 phishing in test); the
exact counts are in `evaluation.json`.

The gap between grouped and random F1 is 0.1 points. A model that had merely memorised campaign or sender
identity would show a much larger gap, which is the useful signal here: the features carry real signal beyond
group identity. It does not mean the model generalises to modern mail, and the `auth_missing` artefact above is a
large part of why the signal looks so clean.

## What this does and does not establish

Establishes:

- The extractor runs end-to-end on real mbox/tarball corpora and produces a usable 65-feature matrix.
- Host- and sender-grouped separation is meaningful: performance holds when whole campaigns and whole sender
  domains are withheld.
- Recall on unseen campaigns is high enough that the explainability layer has something worth explaining.

Does not establish:

- Production accuracy. Corpus labels are corpus-of-origin, the data is 15-20 years old, and there is no
  independent holdout from a third party.
- Stability. One split, one seed, no confidence intervals or bootstrap. A single-split F1 of 0.987 has no error bar
  attached in this repository yet.
- Anything about attachments, images, QR codes, or modern authentication-header failures, which the corpora barely
  contain.
- That the shipped model behaves like this. The shipped model is the synthetic demo model; these metrics belong to
  the evaluation comparator.

## Reproducing

The split seeds, group derivation, and threshold selection are fixed in `training/evaluate.py`, so a rerun on the
same corpora reproduces these numbers bit-for-bit on the same library versions. Library versions are not pinned by
`requirements.lock.txt` in CI, so cross-version drift is possible.

## Known gaps

- No bootstrap confidence intervals, so no honest way to claim two configs differ.
- No per-feature-group ablation (header vs URL vs text vs action) on real data.
- No third-party holdout; every number here comes from the same two corpora used for tuning decisions.
- Dataset licences fit academic use; redistribution and commercial use need upstream review.

## Promoted serving model (measured the same way)

`training.train --source corpus` on this dataset with the 65-feature extractor selected **xgboost**
(`xgboost-corpus-20261110-s7`). Held-out test metrics after isotonic calibration (986 rows, fit 2,647 /
validation 628 / test 986): precision 0.965, recall 0.989, F1 macro 0.978, FPR 0.033, ROC-AUC 0.993,
PR-AUC 0.986, Brier 0.014, confusion TN/FP/FN/TP = 499/17/5/465. Before calibration the same model scored
F1 macro 0.987 and PR-AUC 0.999.

The 2026-11-06 run on the earlier 57-feature vector scored F1 macro 0.983 and PR-AUC 0.984 for the same
procedure. The two runs differ in feature set, so this is not a controlled comparison; the whole-corpus
`training/evaluate.py` comparator on the 65-feature matrix reports F1 0.987 and PR-AUC 0.999.

The training artifact is `backend/models/active/` and the run record is `backend/reports/training_report.md`
(both gitignored). It is **not** in the Docker image yet: Render still bakes the synthetic demo model. Shipping it
is the manual step in `docs/18-open-manual-actions.md` and `docs/19-teammate-training-guide.md` step 8, and it comes
with the `auth_missing` caveat above, which is why it is a decision and not a formality.

### Per-group ablation (65 features, XGBoost)

Dropping one group at a time and refitting, macro F1 on the same test slice:

| Group dropped | Macro F1 | ROC-AUC |
|---|---|---|
| header | 0.972 | 0.996 |
| url | 0.983 | 0.998 |
| text | 0.981 | 0.997 |
| action | 0.989 | 0.999 |
| attachment | 0.985 | 0.999 |
| behaviour | 0.987 | 0.998 |

Header and URL remain the load-bearing groups; action and attachment add little on these corpora, which contain
few executable attachments and little marketing-style mail. That is a property of the corpora, not evidence that
those groups are useless on modern mail.
