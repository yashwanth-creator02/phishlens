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
| Phishing (Nazario) | 1,390 | 819 | campaign / first URL host |
| Legitimate (SpamAssassin) | 2,712 | 468 | sender domain |
| Total | 4,102 | 1,287 | |

The corpus is skewed toward legitimate mail (2:1). Labels follow the corpus of origin, which is the usual
labelling shortcut and the main reason these numbers cannot be read as production accuracy: Nazario is
phishing-only by construction and SpamAssassin ham is 2003-era mailing-list traffic, so "legitimate" here means
"not in a phishing corpus", not "a benign modern business email".

Both corpora are old. SpamAssassin ham is dated 2003. The Nazario mbox files cover roughly 2003-2007. Header
habits, URL shorteners, HTML-only bodies, tracking pixels, and attachment patterns of 2020s mail are
underrepresented, so the score measures the pipeline's feature extraction and the corpus separation, not today's
attacker-vs-defender gap.

## Split

Primary result uses `GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)` with groups as above: no
campaign host and no sender domain appears in both train and test. 3,092 train / 1,010 test.

Because a grouped split holds out whole groups by definition, every test sample is a cold-start sample: the report's
`cold_start_f1` is therefore identical to the headline F1, and its `cold_start_n` equals the test size. That is
expected arithmetic, not two independent findings.

A random stratified split on the same rows is reported only as the comparison baseline. It leaks campaign and
sender identity across the split and is not a result.

## Model under evaluation

`training/evaluate.py` trains a throwaway `XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1,
random_state=7)` on the 57-feature matrix produced by the production extractor, then discards it. The serving model
in `backend/models/` (currently a synthetic-data Random Forest) is untouched, and none of these numbers describe it.

## Results

| Metric | Grouped split (headline) | Random split (leaky baseline) |
|---|---|---|
| Precision | 0.968 | - |
| Recall | 0.930 | - |
| F1 | 0.948 | 0.962 |
| PR-AUC | 0.990 | 0.994 |
| FPR at decision threshold | 0.025 | - |

Confusion counts behind grouped F1: 1,010 test samples, 968 precision and 930 recall at the tuned threshold
implies roughly 28 false positives and 38 false negatives per 1,010 messages; the exact counts are in
`evaluation.json`.

The gap between grouped and random F1 is 1.4 points. A model that had merely memorised campaign or sender
identity would show a much larger gap, which is the useful signal here: the features carry real signal beyond
group identity. It does not mean the model generalises to modern mail.

## What this does and does not establish

Establishes:

- The extractor runs end-to-end on real mbox/tarball corpora and produces a usable 57-feature matrix.
- Host- and sender-grouped separation is meaningful: performance holds when whole campaigns and whole sender
  domains are withheld.
- Recall on unseen campaigns is high enough that the explainability layer has something worth explaining.

Does not establish:

- Production accuracy. Corpus labels are corpus-of-origin, the data is 15-20 years old, and there is no
  independent holdout from a third party.
- Stability. One split, one seed, no confidence intervals or bootstrap. A single-split F1 of 0.948 has no error bar
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
