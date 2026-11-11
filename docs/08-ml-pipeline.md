# 08 - ML pipeline

## 1. Data
| Source | Role | Notes |
|---|---|---|
| Nazario phishing corpus | positive class | older campaigns; check dates/leakage |
| Apache SpamAssassin public corpus | negative (ham); spam as hard negatives | spam != phishing |
| Enron corpus | negative class; sender histories for behaviour benchmark | dated (early 2000s) |
| PhishTank | verified phishing URLs for URL-feature work | verified entries only |
| LLM-Nazario / Toth et al. 2025 | robustness test (E4), augmentation | licence permitting |
| Project-collected (consented, anonymised) | end-to-end tests, demos | no personal data retained |
| **Synthetic generator** (`training/synthetic.py`) | **pipeline testing only** | never report its numbers |

Load real corpora with `training/corpus.py` (`.eml`, `.txt`, `.mbox`; exact duplicates removed; group = sender domain).

### Preparation rules
parse with the *production* parser; decode/HTML->text/normalise URLs; remove exact and near duplicates; remove label-leaking artefacts
(footers, file-name patterns); anonymise; spot-check labels; **split by group (sender domain/campaign)** and in time order where dates exist;
cross-dataset tests; keep a realistic imbalanced test set.

## 2. Features (65, six groups) - `backend/app/features/`
Numeric features are scaled to roughly 0-1 in the extractor so linear models and SHAP behave well. Unavailable evidence gets a *missing* flag.
Wording is one group among six: fluent AI-written phishing passes grammar checks.

| Group | Features | What it covers |
|---|---|---|
| header | 13 | SPF/DKIM/DMARC results, From/Reply-To/Return-Path mismatches, brand impersonation, hop count, domain age |
| url | 18 | link count and domain spread, text-vs-target mismatch, IP hosts, shorteners, punycode, subdomain depth, URL length, path depth, ports, percent-encoding, brand-in-subdomain, TLD, http-only, landing domain age |
| text | 10 | urgency, threats, credential phrasing, money terms, caps ratio (body and subject), exclamations, readability, length, generic greeting |
| action | 6 | click / credentials / payment / download / reply-info requests, plus the count of distinct asks |
| attachment | 8 | presence and count, risky and double extensions, macro-enabled Office, MIME mismatch, archives, largest size |
| behaviour | 10 | sender history, new sending/Reply-To/link domains, urgency deviation, text-style distance, reply-without-history, insufficient history |

The full per-feature dictionary, scaling rules, and the model hyperparameters live in
[`20-model-parameters-and-features.md`](20-model-parameters-and-features.md). Keep that page as the single
authoritative list so the two cannot drift.

### Behavioural features (design)
Per (user, sender): message count, mean/variance of urgency (Welford), sets of return-path / reply-to / link domains, centroid of a hashed
character-trigram vector (EMA, alpha = 0.2). For a new message: `z = |x - mu| / max(sigma, 0.15)`, `d_cos = 1 - cos(e, e_centroid)`.
Below `min_history_messages` (default 3) deviation features are 0 and `insufficient_history = 1` (and no behavioural *reason* may be shown).
History is updated **only** from known-good uploads or LOW-risk analyses (ADR-007).

### Behavioural benchmark (why it is semi-synthetic)
Public phishing corpora have no victim-side history from the same sender. Build a benchmark: Enron senders give realistic normal behaviour; inject
phishing / LLM-written messages under known sender identities (spoofed, look-alike, compromised account). State this limitation in any result.

## 3. Models and selection (`training/train.py`)
| Model | Role | Notes |
|---|---|---|
| Logistic Regression | transparent baseline | class-weight balanced |
| Random Forest | non-linear ensemble | 300 trees, depth 12 |
| XGBoost | boosted trees | 300 trees, depth 4, lr 0.08, positive-class weight |
| URL-only Random Forest | **"existing approach" baseline** (simplified re-implementation in the spirit of published URL pipelines) | replace with a faithful re-implementation (e.g. Yi et al. 2026) for the final report |

Procedure: group split -> test (25% of groups) / validation (20% of the rest) / fit. Select on validation: highest macro F1 subject to FPR <= 3%,
tie -> ROC-AUC. **Isotonic calibration** on validation predictions. Report on test: accuracy, precision, recall, F1 (phishing and macro), FPR, ROC-AUC,
PR-AUC, Brier, confusion matrix; **ablation** (drop one feature group, XGBoost). Output: `models/<tag>/` (+ copy in `models/active/`) and
`reports/training_report.md|json`. The model file stores the feature-name list; the API refuses to load a model whose features differ from the code (train/serve skew guard).

Caveat: selection and calibration share the validation split (slightly optimistic); for the final report use nested CV or a separate calibration split.

## 4. Evaluation plan (E1-E8)
See [13-testing-and-evaluation.md](13-testing-and-evaluation.md). Statistics: bootstrap 95% CIs, McNemar for paired predictions.

## 5. Risk bands
`score = round(100 * p_cal)`; provisional bands LOW <= 29, MEDIUM 30-69, HIGH >= 70 (`PHISHLENS_BAND_*`). Final thresholds from validation data:
choose `t_high` so HIGH-band precision >= 0.95 and `t_low` so MEDIUM+HIGH recall >= 0.98 (starting rules; revisit with stakeholders). Store the band
used with each analysis so old results stay explainable after retuning.

## 6. Demo-model results (synthetic - NOT evidence)
[demo_training_report_SYNTHETIC.md](demo_training_report_SYNTHETIC.md) is the report produced by `make train-demo` on 2,400 generated emails
(selected: XGBoost, macro F1 about 0.96). It only shows that the pipeline runs end to end: the generator encodes the very patterns the features look for.
Expect much lower, more interesting numbers on real corpora; those are the ones to report.
