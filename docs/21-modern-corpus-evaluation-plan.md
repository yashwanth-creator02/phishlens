# 21 - Modern corpus evaluation plan

**Last updated:** 2026-11-11
**Status:** P0, P1 and P2 complete. P2 failed its gates, so H1 is rejected as sufficient and the ablation route to a
candidate is closed. On 2026-11-11 the owner decided to use the personal mailbox as a modern legitimate-mail training
source, which is the re-plan in section 13, option A. The four-candidate protocol (section 14) has since been run.
**Harness:** `backend/training/evaluate_modern.py`
**Decision owner:** project owner for promotion and privacy; see section 10

This is a decision plan, not a results report. The only measured figures are the baseline in section 4, the P2
ablation in section 7.1, and the artifacts they cite. Every gate is a target, not a result.

**Outcome so far:** the active model cannot be repaired by removing features. No ablation variant comes close to the
FPR gates, so nothing is promoted; the corpora-trained model stays out of the live demo. The binding constraint was
the absence of modern legitimate mail in the training data. The owner resolved it on 2026-11-11 by allowing the
personal mailbox to be used for training, under a privacy constraint; the next candidate is trained with it and must
still clear every P4 gate. See sections 7.1, 12 and 13.

## 1. Purpose and scope

The active model (`xgboost-corpus-20261110-s7`, 65 features, isotonic calibration) scores almost every legitimate
message in a modern Gmail mailbox as phishing: FPR 0.999 at probability 0.5 and at the LOW/MEDIUM boundary, over
2,216 ham messages. The purpose of this plan is to decide, on evidence, whether a model can be made usable on modern
mail, and to define the gates that must pass before any such model is promoted.

In scope:

- A clean, leakage-free baseline of the active model on modern ham.
- A diagnosis of why the model fails, starting with era-feature leakage.
- A bounded set of candidate fixes (feature ablation, retraining, calibration) measured against fixed gates.
- A promotion, stop, or re-plan decision, with the documentation and privacy work that follows either way.

Out of scope:

- A production-accuracy claim. One inbox is not a population.
- Measuring phishing recall in the inbox. Gmail already filtered it; received mail is ham by construction.
- Tuning the 29/70 band thresholds to make the numbers pass. Thresholds are product behavior; gates are defined at
  the current values.
- Any use of mailbox content for model selection, calibration, threshold tuning, or committed artifacts. Training use
  is now permitted by owner decision (2026-11-11, section 3).

Success is one of two outcomes: a candidate that passes every P4 gate and is promoted with approval, or a documented
decision not to ship a modern-mail claim, with the failure mode and the next evidence requirement recorded.

## 2. What this evaluation can and cannot prove

| Question | Can this evaluation answer it? | Why |
|---|---|---|
| Does the active model over-flag modern legitimate mail? | Yes, directionally | 2,216 received messages, same extractor as serving, FPR 0.999. The effect is far too large to be sampling noise. |
| Is the failure caused by era features such as authentication presence? | Yes, by ablation | The P2 variants remove the suspect features and re-measure; the comparison isolates their contribution. |
| Will a fixed model work on modern mail in general? | No | One inbox, one provider, one person, one point in time. Domain-macro FPR and a CI bound the optimism but do not remove it. |
| Will it catch modern phishing? | Partly | Held-out Nazario 2015-2023 is clean for the active model, but it is still a research corpus, not live traffic. |
| Is the 2024-2025 phishing recall real? | No | The active model trained on those years. That number is in-sample and must not be quoted as generalization. |
| Is the false-positive rate acceptable in production? | No | A mailbox is a convenience sample with heavy sender skew; production needs traffic or a multi-user consented sample. |

Two consequences follow. A pass is a floor, not a certification: it says the model is no longer obviously broken on
one modern inbox. A fail is conclusive enough to block promotion, because the observed failure is not marginal.

## 3. Privacy boundary

The mailbox is personal data. Since 2026-11-11 the owner allows it to be used for training, under the constraint
that no sensitive information or personal data may reach a committed artifact or the public deployment.

- Path: `backend/data/raw/mailbox/All mail Including Spam and Trash.mbox` (148 MB). `backend/data/raw/` is
  gitignored, so the file is not tracked.
- `corpus.load_mailbox` filters `X-Gmail-Labels` for Spam, Trash, Sent, Drafts, and Chat. Only received mail is
  loaded.
- The mailbox may be used as a modern legitimate-mail training source (owner decision, 2026-11-11). It must still not
  be used for model selection, calibration, threshold tuning, or a committed artifact.
- Do not print message bodies, subjects, addresses, or Message-IDs in reports, logs, notebooks, or chat. Reports
  contain aggregate counts, rates, and sender domains only.
- A model trained on the mailbox is personal-data-derived. It stays local (`backend/models/` is gitignored) and must not
  be baked into the Docker image or shipped to Render without a separate explicit owner decision.
- Derived matrices in `.tmp/auth_cache/*.npz` are also personal-data derivatives. They were deleted on 2026-11-11;
  delete any new ones at P6.
- The mailbox owner is the data controller. Retention, deletion, and any change of use require their explicit
  approval; see D4.

If the owner withdraws consent, stop the evaluation, delete derived artifacts, and keep only aggregate numbers
already approved for publication.

## 4. Baseline data profile

Measured with the active model and the current harness:

| Item | Value |
|---|---|
| Mailbox file | `backend/data/raw/mailbox/All mail Including Spam and Trash.mbox`, 148 MB |
| Loaded messages | 2,216 |
| Scored messages | 2,216 |
| Date range | 2020-10-21 to 2026-09-12 |
| SPF present | 2,210 (99.7%) |
| DKIM present | 2,205 (99.5%) |
| DMARC present | 1,985 (89.6%) |
| Messages with at least one link | 1,929 (87.0%) |
| FPR at probability 0.5 | 0.999 |
| FPR at the LOW/MEDIUM boundary (reported as 0.29) | 0.999 |
| FPR at the boundary, domain-macro | 0.996 |
| 95% CI (pooled, cluster bootstrap over sender domains) | 0.997 - 1.000 |
| Sender domains | 133 |
| Largest single sender | 701 messages (31.6%) |
| Next three senders | 180, 122, 96 |
| Top four sender domains | about 50% of the scored mailbox |

The sender names are deliberately not written here: they are the subscriber list of a personal inbox, and this
document is committed to a public repository. The per-domain table with the names lives in the local report
artifact (`backend/reports/modern-holdout/evaluation.md`), which is gitignored.

`backend/reports/modern-holdout/evaluation.md` records 2,202 HIGH, 12 MEDIUM, and 2 LOW, so 2,214 of 2,216 cross the
band boundary. The two remaining messages are the only legitimate ones the model does not flag.

Reconciliation note: an earlier count of 2,220 loaded came from a loader state without body-hash deduplication. The
current loader deduplicates by raw hash, Message-ID and body hash and yields 2,216 loaded and scored, which is the
number to quote. The date range above is the one the current harness reports.

## 5. Why domain-macro FPR and a bootstrap CI

A message-level FPR of 0.999 is already unambiguous, but the next model will be judged near 0.05, where the
denominator and the sender mix matter.

- **Domain skew.** One sender domain is 32% of the mailbox and the top four are about half. A message-level rate is
  mostly a rate over those domains. If a candidate fixes the top domain and leaves the rest broken, the
  message-level number improves while the experience for every other sender does not.
- **Domain-macro FPR.** Compute FPR per sender domain, then average the per-domain rates with equal weight. This
  answers "on a typical sender domain, how often is legitimate mail flagged?" and stops the largest domain from
  setting the headline.
- **Cluster bootstrap.** Resample sender domains with replacement, 1,000 times, seed 7, and report the 2.5th and
  97.5th percentiles of the domain-macro rate. Messages inside a domain are correlated, so a message-level interval
  would be too narrow. The interval is a stability check on one inbox, not a population interval.

The macro average is sensitive to small domains: a domain with one message contributes a 0.0 or 1.0 rate with the
same weight as a domain with 701. Report the number of domains and the share of messages in domains with fewer than
five messages. Do not silently drop small domains; if a minimum is applied, state it and the excluded count.

One definition: the LOW/MEDIUM boundary is `score > 29`, and `to_score` rounds `100 * p`. This plan reports that
boundary as FPR@0.29. P0 records both the probability threshold and the band boundary so the two cannot drift apart.

## 6. Leakage analysis

The active model's modern-phish recall is contaminated.

- `backend/models/active/meta.json` names `xgboost-corpus-20261110-s7`; the training corpus includes Nazario
  `phishing-2024` and `phishing-2025`.
- `backend/reports/modern/evaluation.json` scores 787 phish messages from 2024-01-01 to 2026-01-01 and reports
  recall 0.999. The model trained on 2024 and 2025. That 0.999 is memorization of campaigns it already saw, not
  generalization.
- The clean modern-phish window for this model is 2015-2023: nine years it never trained on. That is the only
  modern-phish recall this plan may use as evidence.
- The same logic applies to any future retrain. If a new model trains on 2024-2025, those years stop being a test
  set.

| Window | Role for the active model | Role for a P3 candidate |
|---|---|---|
| Pre-2015 (`phishing0`, `phishing1`, `phishing2`) | Training (already seen) | Training only |
| 2015-2023 | Unseen; clean modern-phish test | Unseen; clean modern-phish test |
| 2024-2025 | Seen; in-sample, do not quote | Unseen if the candidate trains on pre-2015 only |
| Mailbox 2020-2026 | Ham test only | Before 2024 may train; 2024 and later is held out |

**Temporal holdout rule.** Adopt this for every future model:

1. Choose a cutoff date before training. Everything before it may train; everything after it is test.
2. Never train on a message dated on or after the cutoff, including through a near-duplicate campaign.
3. Record the cutoff, the source files, and the message counts in `meta.json` and the training report.
4. Deduplicate by raw hash, Message-ID, and body hash before splitting; a campaign copied into two files is still
   one campaign.
5. If a new corpus arrives, assign it to train or test by date first, not by convenience.
6. Evaluate on the same fixed test windows across runs so results stay comparable.

For the current work the cutoff is 2015-01-01: pre-2015 trains, 2015-2023 tests. The 2024-2025 archive is an
additional unseen window only if the candidate does not train on it.

## 7. Hypotheses

| ID | Hypothesis | Why it is plausible | Evidence that confirms it | Evidence that rejects it | Status |
|---|---|---|---|---|---|
| H1 | Era-feature leakage is the primary cause. The model learned "authentication missing" as legitimate because 2003 SpamAssassin ham has `auth_missing=1` on nearly 100% of messages, while only about 1.1% of modern Nazario phishing does. On modern mail, legitimate messages pass authentication, so they land in the phishing region. | The inversion is measured in [19](19-teammate-training-guide.md) and [15](15-risks-and-limitations.md); related era features are `from_returnpath_mismatch` and `http_only`. | A P2 variant that removes the 7 authentication features, or the 9 era features, cuts modern FPR to the P4 gates while held-out 2015-2023 recall stays at or above 0.90 and historical grouped macro-F1 stays at or above 0.95. | FPR stays above the gates after ablation, or recall/F1 collapses, or the full model and the ablated model rank modern ham similarly. | Rejected as sufficient (measured 2026-11-11, section 7.1): dropping the 7 authentication features leaves FPR@0.29 at 0.971, and the 9-feature and header-group variants stay above 0.93. The inversion is real but it is not the cause. |
| H2 | Calibration is a secondary contributor. The calibrated probability, not the ranking, pushes scores over 0.29. | Isotonic calibration is monotone, so it cannot create separation; it can only move the threshold crossing. If raw scores are mostly below 0.29 and calibrated scores are above, recalibration is a partial fix. | Raw and calibrated distributions differ at the 0.29 boundary for the same messages; refitting the calibrator on era-matched data reduces FPR without a recall loss. | Raw probabilities are already near 1.0 for the same messages; recalibration changes almost nothing. | Rejected (measured 2026-11-11): on the 2,216 mailbox messages the uncalibrated probabilities average 0.967 and 99.7% are already above 0.29; calibration moves only 0.18% of messages across the boundary. |
| H3 | Domain skew distorts the headline. A few high-volume senders dominate the message-level FPR. | The largest sender is 32% of the mailbox and the top four are about half. | Domain-macro FPR is materially lower than message-level FPR, and the failures concentrate in a small number of domains. | Domain-macro FPR is close to the message-level rate; failures are spread across domains. | Rejected (measured): domain-macro FPR@0.29 is 0.996 against a message-level 0.999, and the ten worst sender domains are each at 1.000. The failures are spread, not concentrated. |

H1 is the primary hypothesis because the feature statistics invert between the training era and modern mail. H2 and
H3 are checked so that a fix is not credited to the wrong cause. A fourth possibility, a pipeline or labeling bug, is
covered by P0 and is not treated as a hypothesis.

The 7-feature mask drops pass, fail, and missing together. The era signal is the joint distribution of all of them,
not one column. The 9-feature mask adds `from_returnpath_mismatch` and `http_only`.

### 7.1 P2 result - the ablation, measured

The diagnostic is `.tmp/auth_blind_experiment.py`; it trains on pre-2015 Nazario phishing plus SpamAssassin ham
(633 `spamassassin.taint.org` messages excluded, grouped split by campaign host and sender domain, seed 7), holds out
2015-2023 and 2024-2025 phishing, and scores the same mailbox with the same 65-feature extractor. It writes only into
`.tmp/auth_cache`; the variant models are never copied to `models/active`.

| Variant | Historical macro-F1 | Mailbox FPR@0.5 | Mailbox FPR@0.29 | 2015-2023 recall@0.29 | 2024-2025 recall@0.29 |
|---|---:|---:|---:|---:|---:|
| `full_65` (no drop) | 0.935 | 0.964 | 0.967 | 0.924 | 0.901 |
| `no_auth_7` | 0.930 | 0.968 | 0.971 | 0.930 | 0.913 |
| `no_auth_mismatch_8` | 0.954 | 0.929 | 0.938 | 0.885 | 0.863 |
| `no_auth_era_9` | 0.928 | 0.968 | 0.971 | 0.927 | 0.903 |
| `no_header_group` (ceiling test) | 0.905 | 0.866 | 0.955 | 0.959 | 0.975 |

Gate comparison for the P2 pass criteria: mailbox FPR@0.5 <= 0.05, FPR@0.29 <= 0.12, 2015-2023 recall@0.29 >= 0.90,
historical grouped macro-F1 >= 0.95.

- **FPR gate: failed by every variant.** The best variant reaches 0.938 against a gate of 0.12, roughly eight times
  the limit. Dropping all seven authentication features does not move it (0.971); dropping the whole header group
  (which also removes genuine signals such as `received_hops` and reply-to mismatch) still leaves 0.955.
- **Recall gate: met by four of five variants**, so the failure is not a blind model. `no_auth_mismatch_8` keeps
  0.885, which is the only recall regression, and it buys the smallest FPR improvement of any variant.
- **Historical macro-F1 >= 0.95: met by `no_auth_mismatch_8` only** (0.954), and only because it trades recall.
- **Brier was not computed per variant** in this run, so that gate is unmeasured rather than failed. The macro-FPR
  gate is likewise unmeasured per variant; the harness computes it for the served path (section 7.2).

**Verdict: the P2 gate is failed, therefore H1 is rejected as stated.** Authentication-header leakage is real and
measurable in the feature statistics, but it is not the cause of the failure. The diagnosis from the same run is
that modern legitimate mail differs from 2003 ham on many features at once, not only on the authentication columns.
Measured on 40 messages per class with the active model:

| Feature | 2003 SpamAssassin ham | Modern mailbox ham | Nazario phishing 2015-2023 |
|---|---:|---:|---:|
| `spf_pass` | 0.00 | 0.98 | 0.00 |
| `dkim_pass` | 0.00 | 0.98 | 0.05 |
| `dmarc_pass` | 0.00 | 0.98 | 0.00 |
| `auth_missing` | 1.00 | 0.03 | 0.10 |
| `http_only` | 0.93 | 0.10 | 0.80 |
| `from_returnpath_mismatch` | 0.65 | 0.15 | 0.43 |
| `requests_click` | 0.00 | 0.55 | 0.75 |
| `max_url_length` | 0.16 | 0.86 | 0.39 |
| `subject_reply_without_history` | 0.55 | 0.00 | 0.08 |

The classifier has never seen a message that looks like a modern legitimate message, so "modern legitimate" is not
a region it can represent. The remedy is data, not a mask: modern legitimate mail has to be in the training set.
The owner allowed the personal mailbox to be used for exactly that on 2026-11-11 (section 3), with a temporal split:
before 2024 trains, 2024 and later is held out.

Two more measurements close the diagnosis:

- **The model is not blind.** On the clean 2015-2023 holdout (2,072 phishing messages it never trained on) recall at
  the LOW/MEDIUM boundary is 0.994. The combined macro-F1 over that window plus the 2,216 legitimate messages is
  0.649, and every point of the shortfall is the legitimate side.
- **Calibration is not the cause.** On the same 2,216 legitimate messages the uncalibrated probabilities average
  0.967, 99.7% of them are already above 0.29, and only 0.18% cross the boundary because of calibration. The ranking
  itself places modern legitimate mail in the phishing region, so refitting the calibrator cannot fix it.

### 7.2 What is now built into the harness

P0 items that are implemented, with tests in `backend/tests/test_evaluate_modern.py`:

- Domain-macro FPR with a cluster bootstrap over sender domains (1,000 resamples, seed 7) and the number of
  sender domains plus the largest domain share, so a headline rate cannot hide behind one dominant sender.
- Raw and calibrated probability summaries recorded side by side, so the calibration hypothesis is checkable in
  the tool rather than in a one-off script.
- Explicit `fpr_at_0_29` and `recall_at_0_29` fields, so the gate table in section 9 can be read straight off the
  report artifact instead of being reconstructed from the band boundary.
- A leakage guard that fails closed. `training.train` records the phishing date range and the mailbox it trained
  on in `meta["training"]`; the harness refuses to report a window the model trained on
  (`--allow-training-overlap`), and also refuses a model that carries **no** provenance, because such a model
  cannot be shown to be disjoint (`--allow-unknown-provenance`). This second case is not hypothetical: the
  pre-provenance serving model trained on the full Nazario corpus, so a default run would have reported its
  in-sample 2024-2025 recall as generalization.
- The ham side of the guard compares mailbox identity, not only dates: a model trained on one mailbox file and
  evaluated on another is recorded as `distinct`, because two files cannot share messages.
- Fail loudly: a phishing window or a mailbox window that yields no messages exits with an error instead of
  writing a ham-only report that looks successful, and a missing file is distinguished from an empty window.
- `--model` points the harness at a candidate model directory, so a candidate is scored before it is promoted.
- `--activate` gates promotion in `training.train`. Without it, a training run writes a candidate directory and
  leaves `models/active` untouched, so an offline run cannot replace the serving model. The promotion copies to
  `active.new` and swaps, so a failed copy leaves the previous model servable, and it refuses a model trained on
  personal mail unless `--allow-personal-data` is passed.

Two items remain open. The cross-split overlap check is not implemented: the corpus loader deduplicates by raw
hash, Message-ID and body hash within a load, which covers an exact copy of a message, but a campaign reworded
across two files would not be caught, and the same attacker domain can sit on both sides of the temporal cut. The
second is that the corpus dates are noisy - some Nazario archives carry dates from 1970 to 2038 and 65 messages
across the 2015-2025 archives have no `Date` at all, so they are dropped by both the cutoff and the window. Both
caveats belong in any report that quotes a holdout number.

## 8. Plan phases

### P0 - Loaders, metrics, and tests

**Question:** is the measurement trustworthy before it is used to decide anything?

Work:

- Add domain-macro FPR to `backend/training/evaluate_modern.py`, computed from the existing `legit-mailbox-<domain>`
  groups, with per-domain totals beside it.
- Add a cluster bootstrap over sender domains (1,000 resamples, seed 7, 2.5/97.5 percentiles) for the domain-macro
  rate.
- Record raw and calibrated probabilities separately, so H2 can be tested. The harness currently writes only
  calibrated values.
- Record the role of each phish window in the report (`clean_holdout`, `in_sample`, `train`) instead of relying on a
  filename.
- Fail loudly when `--phish-dir` exists but yields zero in-window messages. Today the phish block is silently
  omitted, which produces a ham-only report that looks successful.
- Account for the 2,220 loaded vs 2,216 scored gap and record the reason.
- Add a cross-split overlap check: no raw SHA-256, Message-ID, or body hash may appear in both a training split and a
  test split. Report the overlap count for train-old vs 2015-2023 and vs 2024-2025.
- Add tests in `backend/tests/test_evaluate_modern.py` using synthetic arrays only: domain-macro math, bootstrap
  determinism and interval shape, zero-in-window behavior, raw/calibrated fields. Do not put mailbox content in a
  test fixture. Keep `backend/tests/test_corpus_loading.py` green; it protects the extensionless-file and
  Gmail-label filters.

Command:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests\test_evaluate_modern.py tests\test_corpus_loading.py -q
```

Outputs: updated harness and tests; a report schema that contains `n`, `fpr_at_0_5`, `fpr_at_0_29`,
`domain_macro_fpr_at_0_29`, `domain_macro_ci`, `raw_probability_summary`, `window_role`.

Pass gate:

- Tests green.
- A report from a known input carries every field above.
- The cross-split overlap count is 0 for both windows; any nonzero value is reported and resolved before P1.
- No raw mail, address, or body text in the report or the tests.

### P1 - Clean baseline

**Question:** what does the active model actually do on modern ham and on the clean 2015-2023 phish window?

Commands, from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m training.evaluate_modern `
  --model-dir models `
  --phish-dir ..\.tmp\nazario-test-2015-2023 `
  --phish-since 2015-01-01 --phish-until 2024-01-01 `
  --out reports\modern-holdout

.\.venv\Scripts\python.exe -m training.evaluate_modern `
  --model-dir models `
  --phish-dir ..\.tmp\nazario-test-2024-2025 `
  --phish-since 2024-01-01 --phish-until 2026-01-01 `
  --out reports\modern-insample
```

The second run is labeled in-sample on purpose. Its recall is not evidence; it exists to show the size of the
leakage.

Outputs: `backend/reports/modern-holdout/evaluation.{json,md}` and
`backend/reports/modern-insample/evaluation.{json,md}`. Both are gitignored.

Pass gate:

- The mailbox count and FPR reproduce the section 4 baseline within rounding.
- The clean 2015-2023 recall is recorded with `window_role: clean_holdout`.
- Domain-macro FPR and its interval are present.
- The in-sample run is marked as such.
- No threshold is changed in this phase. The baseline is expected to fail the P4 FPR gates; that is the finding, not
  a reason to tune.

### P2 - Auth-blind ablation

**Question:** does removing the suspect features fix the FPR, and at what recall cost?

The diagnostic exists at `.tmp/auth_blind_experiment.py`. It trains on pre-2015 phishing plus SpamAssassin ham,
holds out 2015-2023 and 2024-2025, and compares variants: `full_65`, `no_auth_7`, `no_auth_mismatch_8`,
`no_auth_era_9`, and `no_header_group`. **It was run on 2026-11-11; the measured table and the verdict are in
section 7.1.**

Run from `backend/`:

```powershell
.\.venv\Scripts\python.exe ..\.tmp\auth_blind_experiment.py
```

Before treating the output as evidence:

- Add a Brier score per variant. The script's `bootstrap_fpr` already resamples sender-domain clusters, but it
  pools messages inside each resample, so it intervals the message-level rate. Add a separate domain-macro FPR and
  its interval; the two answer different questions (section 5).
- Confirm the historical split is grouped by campaign and sender domain, and that the taint exclusion is applied.
- Confirm the variant model is never written to `models/active`.
- Treat `no_header_group` as a ceiling test, not a candidate. It removes genuine header signals such as
  `received_hops` and reply-to mismatch.
- Delete the cache after the run; it contains personal-mail-derived matrices.

Done on 2026-11-11: the split is grouped by campaign host and sender domain, the 633 taint messages are excluded, and
no variant is written outside `.tmp/auth_cache`. Brier per variant and the per-variant domain-macro interval were
not added; both are open.

Pass gate for the diagnosis:

- At least one variant reaches modern FPR@0.5 <= 0.05, FPR@0.29 <= 0.12, and domain-macro FPR@0.29 <= 0.10 on the
  mailbox.
- The same variant keeps held-out 2015-2023 recall@0.29 >= 0.90.
- Its historical grouped macro-F1 is >= 0.95 and Brier <= 0.02.
- If no variant reaches all of these, H1 is not sufficient as stated. Stop and re-plan; do not promote.

**Gate result: failed.** No variant is within an order of magnitude of the FPR limits (section 7.1). Per the last
bullet, P3 does not start on this route and nothing is promoted. The re-plan is in section 13.

### P3 - Retrain and calibrate a candidate

**Question:** can the winning variant become a model that the serving code can actually load?

The winning variant does not exist: the P2 gate failed, so this phase restarts from the re-plan (section 13, option A)
- retrain with the mailbox before 2024 as the modern legitimate-mail source, keeping all 65 features.

Train on pre-2015 only, with the winning mask, into a scratch model directory:

```powershell
.\.venv\Scripts\python.exe -m training.train `
  --source corpus `
  --phish-dir ..\.tmp\nazario-train-old `
  --legit-dir data\raw\spamassassin `
  --drop-features spf_pass,spf_fail,dkim_pass,dkim_fail,dmarc_pass,dmarc_fail,auth_missing,from_returnpath_mismatch,http_only `
  --out models\candidate-era-blind `
  --reports reports\candidate-era-blind
```

`--drop-features` does not exist yet. P3 adds it, or applies the mask in a reviewed scratch script. The command
shows the 9-feature variant; substitute the exact P2 winner. Do not add or remove a feature after seeing the modern
result.

**Shippability constraint.** `app/ml/registry.py` rejects a model whose `meta["feature_names"]` differs from the live
`FEATURE_NAMES`. A training-only drop therefore cannot be served. P3 must choose one honest path:

- Preferred: keep all 65 names and neutralize the era features to documented constants in a versioned serving
  transform, recorded in `meta.json` as a feature mode. The model, the SHAP background, and the serving vector then
  live in the same space.
- Alternative: reduce `FEATURE_NAMES` itself and update the extractor, tests, SHAP, and docs in one change. This
  removes the authentication signal for every future model and is not reversible without another retrain.

A diagnostic drop that is never served is acceptable in P2. It is not acceptable in P3.

Calibration:

- Default: fit isotonic on the historical validation split, as `training.train` already does.
- Do not fit the calibrator on the evaluation mailbox. A model tuned to one inbox is not a general model, and
  calibrating on the gate slice leaks the test.
- If H2 is confirmed and a calibration change is still wanted, calibrate on a public modern ham corpus, or split
  the mailbox by time with pre-2024 for calibration and 2024+ for the gate. The second option is a last resort and
  must be documented as a one-inbox fit.

Outputs: `backend/models/candidate-era-blind/<tag>/` and `.../active/`,
`backend/reports/candidate-era-blind/training_report.{json,md}`. The scratch model directory is gitignored.

Pass gate:

- Training completes with 65 names (preferred path) or the reduced set (alternative path), and the registry loads it.
- The candidate's saved metadata records the cutoff, the source files, the feature mode, and the mask.
- The historical test metrics are written before any modern test is run.

### P4 - Candidate gates

**Question:** does the candidate pass every gate at once?

Run the harness against the candidate, not the active model:

```powershell
.\.venv\Scripts\python.exe -m training.evaluate_modern `
  --model-dir models\candidate-era-blind `
  --phish-dir ..\.tmp\nazario-test-2015-2023 `
  --phish-since 2015-01-01 --phish-until 2024-01-01 `
  --out reports\candidate-era-blind\modern
```

Numeric gates, all mandatory:

| Gate | Threshold | Measured on |
|---|---|---|
| Usable ham | >= 1,500 messages | Mailbox, after filtering |
| Modern FPR@0.5 | <= 0.05 | Mailbox ham |
| Modern FPR@0.29 | <= 0.12 | Mailbox ham |
| Modern domain-macro FPR@0.29 | <= 0.10 | Mailbox ham, equal domain weight |
| Held-out modern-phish recall@0.29 | >= 0.90 | Nazario 2015-2023 |
| Historical grouped macro-F1 | >= 0.95 | Pre-2015 phish + SpamAssassin ham, P3 training report |
| Brier | <= 0.02 | Historical calibrated test, P3 training report |
| Demo samples | `legit_*.eml` score <= 29 | API or direct scoring |
| Backend tests | All pass | `python -m pytest -q` |

The sample check, from `backend/` with the candidate as the model directory:

```powershell
$env:PHISHLENS_MODEL_DIR = "models\candidate-era-blind"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
curl.exe -X POST http://localhost:8001/api/analyses/upload `
  -F "file=@data/sample_emails/legit_newsletter.eml"
curl.exe -X POST http://localhost:8001/api/analyses/upload `
  -F "file=@data/sample_emails/legit_bank_alert.eml"
```

Check the `score` field, not the band alone. Stop the server and release the port afterwards. If the API path is
inconvenient, score the two files directly through the same extractor and registry; do not bypass either. These are
demo files, not evidence about real mail; they are a smoke test that the era inversion is gone.

Pass gate: every row passes in the same run. A partial pass is a fail.

### P5 - Promote or stop

If every P4 gate passes:

- Present the baseline, the P2 table, and the P4 table together. The comparison is the evidence, not the
  candidate's headline FPR alone.
- Ask the project owner for explicit approval to promote. This plan does not authorize a merge or a deployment.
- Promote by retraining with `--out models` using the same seed and data, or by copying the candidate tag to
  `models/active`. The previous tag stays under `models/` as the rollback.
- Update the Docker and Render path only if the deployment is in scope; see [19](19-teammate-training-guide.md).
- Verify `/api/health` reports the new `version_tag` and `model_loaded: true`.

If any gate fails:

- Do not promote, do not lower a threshold, and do not re-run variants until one passes. That is gate shopping.
- Record the failing gate, the observed value, and the closest variant in the decision log.
- Choose the next evidence: a public modern ham corpus, a new feature, or a decision to stop claiming modern-mail
  support.

### P6 - Documentation and privacy cleanup

Documentation:

- Update [15](15-risks-and-limitations.md) with the measured modern FPR and the outcome.
- Update [17](17-real-corpus-evaluation.md) with the in-sample warning and the temporal holdout rule.
- Update [20](20-model-parameters-and-features.md) if the feature mode or the feature set changes.
- Update [19](19-teammate-training-guide.md) so the documented training command matches the served feature mode.
- Add this page to [README.md](README.md) and [FILE_INVENTORY.md](FILE_INVENTORY.md).
- Add an ADR under `decisions/` if a model is promoted or the auth-blind mode is adopted.
- Update [18](18-open-manual-actions.md) only for actions that need the user; remove an item when it is done.

Privacy:

```powershell
Remove-Item -Recurse -Force .tmp\auth_cache
Remove-Item -Force .tmp\auth_blind.out, .tmp\auth_blind.err
```

Run on 2026-11-11: the derived cache was deleted on the owner's instruction, and the raw export stays on disk.

- Keep or delete the raw mailbox only with the owner's instruction. Deleting it does not delete the gitignored
  reports that already contain aggregates.
- Confirm `git status --porcelain` shows no data, model, or report artifact.
- Record the deletion date and the approving owner in the decision log.
- A model trained on the mailbox stays local and is not baked into the Docker image or shipped to Render without a
  separate explicit owner decision.

Pass gate: docs match the shipped behavior; no personal-data derivative remains without an approved retention
reason.

## 9. Gate summary

| Gate | Value | Phase | Applies to |
|---|---:|---|---|
| Usable ham | >= 1,500 | P0/P4 | Mailbox |
| FPR@0.5 | <= 0.05 | P4 | Candidate, mailbox |
| FPR@0.29 | <= 0.12 | P4 | Candidate, mailbox |
| Domain-macro FPR@0.29 | <= 0.10 | P4 | Candidate, mailbox |
| Held-out phish recall@0.29 | >= 0.90 | P4 | Candidate, Nazario 2015-2023 |
| Historical grouped macro-F1 | >= 0.95 | P4 | Candidate, pre-2015 + SpamAssassin |
| Brier | <= 0.02 | P4 | Candidate, historical calibrated test |
| `legit_*.eml` score | <= 29 | P4 | Candidate, both samples |
| Backend tests | all pass | P4 | Repository |

The baseline in section 4 fails the FPR gates by a wide margin. That is expected and is not a P1 failure; P1's job
is to record it cleanly.

### 9.1 The release

Candidate D's configuration was retrained with the current training code, so the released artifact is produced by the
committed code rather than by an earlier run. The retrain reproduced candidate D exactly (macro F1 0.948, ROC-AUC
0.990, PR-AUC 0.985) and the holdout numbers are unchanged (FPR@0.5 0.022, FPR@0.29 0.041, domain-macro 0.112,
recall@0.29 0.810).

The release then moved on to candidate F in section 15, which is what the repository now serves. The release command
is the same either way:

```powershell
.\.venv\Scripts\python.exe -m scripts.release_model --model ..\.tmp\models-F2\xgboost-corpus-20261112-s7 `
    --mailbox "data/raw/mailbox" --allow-personal-data --notes "..."
```

The audit reported 395 sender domains, 400 distinctive subject words, and **0 findings**, and the SHAP background
sample contains **0 personal rows**. The release note in `backend/release/model/release.json` records that result,
so the decision is auditable after the fact rather than only in a commit message.

The Docker image copies `backend/release/model/` into `/app/models/active/`, so a deployment serves the released
model. Without a release it falls back to training the synthetic demo model, so a fresh checkout still starts.

## 10. Decision log and open questions

| ID | Decision | Options | Recommendation | Owner | Status |
|---|---|---|---|---|---|
| D1 | Promote a new model? | Promote only on a full P4 pass; keep the active model and publish the failure; stop the modern-mail claim | Gate-based only. No promotion on a partial pass, and no threshold change to force one. | Project owner | Decided 2026-11-11: the corpora-trained model is **not promoted as it stands**; it stays a documented historical artefact. The owner allows the personal mailbox to be used as a modern legitimate-mail training source, so the next candidate is trained with it and still has to clear every P4 gate before promotion. |
| D2 | Keep the synthetic demo model in Docker/Render? | Keep it until a candidate passes; replace it on promotion; keep it permanently as a plumbing demo | Keep it for now. A demo that flags every legitimate message is worse than an honest synthetic demo. | Project owner | Decided 2026-11-11: the synthetic demo model **stays live for now**. It is replaced only on a full P4 pass and an explicit promotion approval. |
| D3 | Accept the auth-blind trade-off? | Accept if recall and historical F1 gates hold; reject and use era-normalized authentication features; keep authentication and fix the era problem another way | Do not accept a recall loss. Authentication is a real phishing signal; ignore it only if the measured cost is small and documented. | Project owner | Rejected 2026-11-11: the ablation gate failed (section 7.1), so the trade-off was never available - no variant reached the FPR gates at all. The remedy is data, not a feature mask. |
| D4 | Who owns the privacy cleanup? | Mailbox owner approves and deletes; evaluator deletes under written instruction | The mailbox owner is the data controller; the evaluator executes and records the deletion. | Mailbox owner | Done 2026-11-11: on the owner's instruction the derived cache `.tmp/auth_cache` was deleted; the raw mbox export stays on disk. No message content is in any committed artifact. |
| D5 | Change the 29/70 thresholds? | Keep; re-derive on validation data | Keep. The gates are defined at the current product thresholds, and changing them would invalidate the comparison. | Project owner | Proposed: keep; confirm at P5 |

Open questions:

- Is one inbox enough to block promotion? It is enough to reject the current model. It is not enough to certify a
  replacement; the gates are a floor.
- What public modern ham corpus would satisfy the same gates? None is in the repository today. The owner's mailbox is
  now eligible for training, so the candidate uses that; a public corpus would remove the personal-data constraint.
- Does the product need an auth-blind mode, or only an era-balanced model? If auth-blind is diagnostic only, P3's
  shippability constraint changes.
- How long may the mailbox and its derived matrices be retained? The owner decided on 2026-11-11 that the raw export
  stays on disk and the derived cache is deleted. A new cache is deleted at P6.
- Who signs the promotion, and by when? The project owner; no date is set.

## 11. Status

| Phase | Status | Evidence |
|---|---|---|
| P0 Loaders, metrics, tests | Partly done | Harness at `backend/training/evaluate_modern.py`; tests at `backend/tests/test_evaluate_modern.py`. Done: domain-macro FPR with cluster bootstrap, sender-domain count and largest-domain share, raw and calibrated probability summaries, leakage guard, `--model` for candidates. Open: the cross-split overlap check. |
| P1 Clean baseline | Done | `backend/reports/modern-holdout/` (2015-2023 clean window) and `backend/reports/modern-insample/` (2024-2025, labelled in-sample). Both are gitignored. |
| P2 Auth-blind ablation | Done, gate failed | `.tmp/auth_blind_experiment.py` ran on 2026-11-11; results in `.tmp/auth_cache/results.json`, summarised in section 7.1. No variant approaches the FPR gates. H1 rejected as sufficient. |
| P3 Retrain/calibrate | Not started | The P2 ablation route is closed: there is no winning variant to retrain. The re-plan (section 13, option A) retrains with the mailbox before 2024 as the modern legitimate-mail source. |
| P4 Candidate gates | Not started | Blocked on P3. |
| P5 Promote or stop | Stop, pending owner sign-off | The evidence says do not promote the corpora-trained model: it flags 99.9% of modern legitimate mail. The synthetic demo model stays in the image. |
| P6 Documentation/privacy cleanup | In progress | This plan, the risk list and the evaluation docs are updated. The mailbox-derived cache `.tmp/auth_cache` was deleted on 2026-11-11 on the owner's instruction; the raw export stays on disk (D4). |

## 12. What would change the plan

- Usable ham drops below 1,500, or the owner withdraws consent. Stop; no FPR claim; delete derived data.
- **No P2 variant meets the FPR and recall gates together. This happened on 2026-11-11.** H1 is insufficient as
  stated; do not promote. The owner then allowed the personal mailbox to be used for training, which is the re-plan in
  section 13, option A.
- A variant meets the FPR gates but held-out 2015-2023 recall falls below 0.90. The model is blind, not fixed.
  Reject the auth-blind trade-off and try era-normalized authentication features instead.
- Historical grouped macro-F1 falls below 0.95 or Brier exceeds 0.02. The candidate is worse on the old
  distribution; the trade-off is not acceptable.
- A public modern ham corpus with real authentication headers becomes available. It can enter training alongside the
  approved mailbox slice and would remove the personal-data constraint; re-run P2/P3 with a new cutoff and a new test
  window.
- The active model is retrained on any 2024 or 2025 data. Those years become in-sample again; update the window
  role table before quoting any recall.
- The 29/70 band thresholds change. Every gate is threshold-specific; re-derive the gates before evaluating, and
  never change a threshold to pass a gate.
- A consented production-traffic sample becomes available. It is a better FPR estimate than one inbox; add it as a
  separate test set, not as a replacement for the gates.

## 13. Re-plan after the failed P2 gate (2026-11-11)

The failed gate sends the work down a different branch, so the remaining options are listed with what each one costs.

| Option | What it buys | What it costs | Status |
|---|---|---|---|
| A. Get real modern ham into training | The only option that fixes the root cause: the model finally sees what modern legitimate mail looks like | Needs a corpus that is real and modern. No licence-clean public one exists today, so the source is the owner's personal mailbox, which makes the trained model personal-data-derived | **Chosen by the owner on 2026-11-11**, with a privacy constraint: no sensitive information or personal data may reach a committed artifact or the public deployment |
| B. Synthetic modern augmentation | Cheap: the repository already generates synthetic mail. It would teach the model that authenticated modern mail is not automatically phishing | Synthetic mail cannot be evidence of real-world accuracy, and the published modern "spam/ham" datasets that claim realistic headers say on their own data card that they are generated | Rejected as a source of claims; possible as a labelled experiment |
| C. Public mailing-list archives | Real modern mail with real authentication headers, free and no login | The traffic is human-to-human list mail, not marketing or notification mail, and it carries `List-*` headers that become their own artefact | Not attempted |
| D. Keep the corpora model as a historical artefact and stop claiming modern-mail support | Honest, zero further work, and the strongest story for a viva: the pipeline, the reason engine, the security model and an honest evaluation with a measured failure | The product's headline metric stays a demo metric; no accuracy claim | Fallback if the option-A candidate fails the gates; the corpora model is not promoted either way |

Searches run on 2026-11-11 that support the table: the SpamAssassin public corpus ends at `20050311` (the 2003
archives are what the repository uses); the modern "spam/ham" datasets with 2024-2025 metadata describe themselves as
generated, with no real emails; the public phishing datasets are pre-2008 research corpora or generated text.

**The decision (owner, 2026-11-11): option A.** The owner allows the personal Gmail Takeout mailbox to be used as a
modern legitimate-mail training source. The constraint is privacy, not permission: no sensitive information or personal
data may end up in committed artifacts or in the public deployment. Concretely, the trained model stays local
(`backend/models/` is gitignored), it must not be baked into the Docker image or shipped to Render without a separate
explicit decision, and reports and documentation may contain aggregate counts only, never message content, addresses,
subjects or Message-IDs.

The evaluation design that keeps the measurement honest is a temporal split on the mailbox itself: messages dated
before 2024 may train the candidate, and 2024 and later are held out and never seen in training. A candidate that
passes the gates on that holdout has demonstrated something the current model cannot.

A personal-data-trained model must not be published to the public deployment. Until a candidate passes the P4 gates
and the owner approves promotion, the synthetic demo model stays live (D1, D2 in section 10).

## 14. The four-candidate protocol (2026-11-11)

The re-plan needs one variable changed at a time, and the obvious axis is how much modern legitimate mail the
candidate sees. Four candidates were trained on the same protocol and scored on one shared holdout.

### 14.1 The split

The phishing side is split by **archive file**, not by message date. The corpus dates are not fit for it: some Nazario
archives carry dates from 1970 to 2038, and 65 messages in the 2015-2025 archives have no `Date` at all, so a
date-based cutoff silently admits holdout messages into training and then calls them held out. Thirteen archives up
to 2023 train; the 2024 and 2025 archives are the phishing holdout.

The ham side is split by **date**, which the real inbox dates support.

| Candidate | Modern ham in training | Ham total | Algorithm |
|---|---|---:|---|
| A | inbox 1, before 2024 | 731 | random forest |
| B | A + SpamAssassin 2003 | 3,443 | xgboost |
| C | both inboxes, before 2026 | 2,579 | random forest |
| D | C + SpamAssassin 2003 | 5,291 | xgboost |

Every candidate is scored on the same holdout: ham from 2026 in both inboxes, and the 2024 and 2025 phishing
archives. No candidate trained on any of it.

### 14.2 What the numbers say

| Candidate | Ham FPR@0.5 | Ham FPR@0.29 | Domain-macro FPR@0.29 | Phish recall@0.29 | Historical macro-F1 | Combined F1@0.5 |
|---|---:|---:|---:|---:|---:|---:|
| A | 0.263 | 0.314 | 0.486 | 0.958 | 0.885 | 0.644 |
| B | 0.071 | 0.179 | 0.386 | 0.900 | 0.933 | 0.770 |
| C | 0.008 | 0.018 | 0.074 | 0.720 | 0.951 | 0.744 |
| D | 0.022 | 0.041 | 0.112 | 0.810 | 0.948 | 0.806 |
| Gate | <= 0.05 | <= 0.12 | <= 0.10 | >= 0.90 | >= 0.95 | - |

The three candidates fail in three different ways, and that is the useful part of the table.

- **A** (modern ham only, one inbox, pre-2024) keeps phishing recall at 0.958 and flags 26% of legitimate mail.
- **B** (A plus SpamAssassin 2003 ham) cuts the false-positive rate to 0.071 by restoring ham diversity, and pays for
  it in recall, which falls to exactly 0.900.
- **C** (both inboxes, before 2026, no 2003 ham) passes all three false-positive gates with room to spare: 0.008 at
  probability 0.5 and 0.074 domain-macro, the only candidate under the domain-macro limit of 0.10. Its recall is
  0.720, which fails the 0.90 gate.
- **D** (C plus SpamAssassin 2003 ham) is the best combined performer: F1 0.806 against 0.744 for C, with recall
  0.810. Its domain-macro rate, 0.112, misses the 0.10 gate by 0.012.

C is the informative one. It proves the false-positive failure is fixable with data: put real modern legitimate mail in
training and the false-positive rate collapses by a factor of thirty. What it does not do is keep phishing recall,
because a model trained on modern mail and old phishing has learned that the notification and list mail that dominates
a real inbox is normal, and some of the older phishing campaigns look like that.

### 14.3 Which gates pass, and by how much

| Gate | Threshold | A | B | C | D |
|---|---:|---:|---:|---:|---:|
| Usable ham | >= 1,500 | pass | pass | pass | pass |
| Modern FPR@0.5 | <= 0.05 | fail | fail | **pass** | **pass** |
| Modern FPR@0.29 | <= 0.12 | fail | fail | **pass** | **pass** |
| Domain-macro FPR@0.29 | <= 0.10 | fail | fail | **pass** | fail by 0.012 |
| Modern-phish recall@0.29 | >= 0.90 | **pass** | **pass** | fail by 0.180 | fail by 0.090 |
| Historical macro-F1 | >= 0.95 | fail | fail | **pass** | fail by 0.002 |
| Brier | <= 0.02 | fail | fail | fail | fail |
| `legit_*.eml` score | <= 29 | fail | fail | fail | **pass** |

**No candidate passes every gate.** The closest is C, which passes five of seven and fails recall by 0.180 and Brier
by 0.004. D fails the same two, by less on recall, and passes the two FPR gates that C also passes.

The Brier gate is failed by all four, at 0.024 to 0.039 against a limit of 0.02. The isotonic calibrator is fitted on a
validation split that mixes 2003 ham with modern ham, and the two have very different score distributions, so the
mapping is poor for one of them. This is a calibration problem with a known fix (fit on one era, or drop the
calibrator and use a threshold on the raw probability), not evidence that the model does not separate the classes: the
ROC-AUC of 0.961 for D is unaffected by the calibrator.

### 14.4 The demo-sample gate, and what the fixtures had to become

The gate asks the two hand-written legitimate fixtures to score at most 29. All four candidates scored them 53 to 100
at first. The cause was not the era inversion the gate was written to detect; it was that the fixtures were not
representative of modern mail.

Measured against the owner's inbox, real modern mail carries two to four `Received` headers and nine to eleven
headers in total, several links with long tracking parameters, and a body of several hundred characters. The
original fixtures carried one `Received` header, six headers, one short link, and a two-sentence body. Their SHAP
contributions were dominated by `received_hops` (+3.06 on the newsletter) and by `financial_terms_ratio` on the bank
alert.

The fixtures were rewritten to the shape real modern mail has, measured against the inbox rather than against the
score. Both now sit inside the real 5-95% range on every feature and score LOW: the newsletter 3, the bank alert 18.
Both phishing fixtures still score HIGH.

The honest caveat: this changes the test input, not the model, and a fixture that passes proves the model handles
that shape of mail. The real evidence for the model is the 2,865-message holdout, not two files. The fixture gate is
worth keeping as a smoke test that the era inversion is gone; it is not evidence of accuracy.

One real limitation surfaced while doing this and is recorded rather than hidden: the extractor matches credential
phrases as plain substrings, so a legitimate warning ("never reveal your OTP") reads as a credential request. It
fires on 3.9% of real modern mail, and those messages still score LOW, so it is a nuisance rather than a defect
today. A negation-aware match would be the fix.

### 14.5 What each side of the failure tells us

The false positives are concentrated in modern legitimate mail that the model has no modern legitimate counterpart
for. The per-domain table shows the pattern: notification and list mail (bank alerts, job portals, newsletters,
GitHub notifications) is flagged at 0.6 to 1.0, while plain mail from major senders sits near 0.12. The model has
learned a phishing shape from the phishing corpus, and the shape of modern legitimate mail falls inside it.

This is the same failure the P2 ablation could not fix, now with a different lever: the lever is not which features
are visible but whether modern legitimate mail is in the training set at all.

### 14.6 The promotion decision

The gates were written to stop a model that cries wolf. Candidate D does not cry wolf: it flags 2.2% of legitimate
mail at probability 0.5 and 4.1% at the triage boundary, against a baseline that flagged 99.9%. On the combined
holdout of 3,653 messages it reaches F1 0.806 with ROC-AUC 0.961.

It also misses 19% of held-out phishing at the triage boundary, against a 10% allowance. That is the trade the owner
is being asked to accept, and it is why the decision is recorded here rather than buried in a commit message:

- **Against promotion**: recall 0.810 against a 0.90 gate, Brier 0.039 against 0.02, domain-macro FPR 0.112 against
  0.10. A triage tool that misses a fifth of phishing is dangerous in exactly the way a false-positive machine is.
- **For promotion**: the alternative is the synthetic demo model, which is not a detector at all. D is measurably
  better than what is live, on a held-out split, on real mail.
- **What the evidence does not support**: any accuracy claim. One inbox, one provider, one person, and a phishing
  corpus that is 20 years old.

The owner's decision on 2026-11-11 was to allow a personal-mailbox model to be published if it carries no personal
data. The audit is that gate: it proves the artifact is clean. The accuracy gates above are a separate matter, and the
numbers are recorded here so the choice is visible rather than implied.

## 15. The Kaggle corpora (2026-11-12)

The owner's instruction was to add Kaggle datasets to the training. What the survey found is that most Kaggle
phishing datasets cannot feed this pipeline, and the ones that can add phishing volume from the era the model already
handles. `docs/datasets/README.md` records which datasets were used and why the others were rejected.

Three corpora were ingested and are usable: CEAS 2008 (20,874 phishing, 17,293 ham), the Nigerian 419 scams (2,720
phishing), and a Kaggle repackaging of SpamAssassin (1,701 phishing, 4,087 ham). They were rebuilt from CSV into real
`.eml` messages, because the feature extractor reads raw messages and these datasets ship the email split across
columns.

Two candidates were trained against the released configuration, on the same shared holdout as section 14.

| Candidate | Training | Ham FPR@0.5 | Ham FPR@0.29 | Domain-macro | Phish recall@0.29 | Combined F1@0.5 | ROC-AUC |
|---|---|---:|---:|---:|---:|---:|---:|
| D (released) | Nazario + SpamAssassin + inbox | 0.022 | 0.041 | 0.112 | 0.810 | 0.806 | 0.961 |
| E | D + Kaggle phishing | 0.004 | 0.013 | 0.045 | 0.674 | 0.703 | 0.967 |
| F | E + Kaggle ham | 0.018 | 0.021 | 0.068 | 0.770 | 0.829 | 0.967 |

### 15.1 What E shows, and why it is not the win it looks like

E's false-positive numbers are the best of any candidate: 0.4% at probability 0.5 and 1.3% at the triage boundary,
and the domain-macro rate of 0.045 passes the gate that D misses at 0.112. Its ROC-AUC of 0.967 is also better than
D's 0.961, so the *ranking* of modern messages improved.

What got worse is recall: 0.674 at the triage boundary against D's 0.810. The cause is visible in the training set.
E adds 23,579 phishing messages to D's 3,516, so the class balance moves from 40% phishing to 84%. The model is
trained mostly on phishing, its calibrated probabilities shift with the prior, and the operating point moves along a
curve that was already better than D's.

That is the honest reading: **E is not a better model at the same operating point, it is a better model at a different
one.** A candidate that is only better because its threshold moved is not a candidate worth promoting, and the fix is
class balance rather than more data.

### 15.2 F: the balance restored, and the best model measured

Adding the Kaggle ham side restores the balance (27,095 phishing against 23,933 ham) and F is the best model
measured so far. Against the released model D:

| Measurement | D | F | Gate |
|---|---:|---:|---|
| Ham FPR@0.5 | 0.022 | **0.018** | <= 0.05, both pass |
| Ham FPR@0.29 | 0.041 | **0.021** | <= 0.12, both pass |
| Domain-macro FPR@0.29 | 0.112 | **0.068** | <= 0.10: **D fails, F passes** |
| Phish recall@0.29 | **0.810** | 0.770 | >= 0.90: **both fail** |
| Phish recall@0.5 | 0.728 | **0.754** | - |
| Combined F1@0.5 | 0.806 | **0.829** | - |
| Combined F1@0.29 | 0.827 | **0.835** | - |
| ROC-AUC | 0.961 | **0.967** | - |
| PR-AUC | 0.877 | **0.906** | - |
| Historical grouped macro-F1 | 0.948 | **0.966** | >= 0.95: **D fails, F passes** |
| Brier | 0.039 | **0.026** | <= 0.02: **both fail** |
| Demo fixtures | 3 and 18 | 6 and 6 | <= 29, both pass |

F wins on every measurement except phishing recall at the triage boundary, where it gives up 0.040 of recall for
half the false positives. It passes two gates that D fails (domain-macro FPR and the historical grouped F1) and it
was audited clean: 395 sender domains, 400 distinctive subject words, **0 findings**, and 0 personal rows in the SHAP
background sample.

The two gates F still fails are the two D also fails, and F is closer on the Brier. The recall gate is the honest
limit: F misses 23% of held-out phishing at the triage boundary against a 10% allowance.

### 15.3 What the corpora did and did not buy

The Kaggle corpora are 2002-2008 material, so they added phishing volume from the era the model already handled
rather than modern campaigns. What they did buy is real: F's ROC-AUC is 0.006 better and its PR-AUC 0.029 better
than D's on the same holdout, and the historical grouped F1 rose from 0.948 to 0.966.

What they did not buy is a single message from the 2015-2025 campaigns. The recall gap is a data-vintage problem,
not a corpus-size problem, and it will not close with more 2008 phishing. Closing it needs either modern phishing
with full headers, which no free public source currently provides, or a second modern inbox to widen the legitimate
side and let the model trade precision for recall on the right distribution.

### 15.4 The promotion decision for F

F was released on 2026-11-12, replacing candidate D. The reasoning is recorded here because the choice is a trade
and a trade should be visible:

- **For**: F is better on eleven of the twelve measurements, it passes two gates D fails, its false-positive rate on
  real modern mail is 1.8% instead of 2.2%, and the privacy audit reports 0 findings with 0 personal rows in the
  artifact. The alternative was the synthetic demo model, which is not a detector at all.
- **Against**: phishing recall at the triage boundary falls from 0.810 to 0.770, and the Brier score is 0.026 against
  a 0.02 gate. Both gates still fail; F is closer on the Brier and further on the recall.
- **What the evidence does not support**: any accuracy claim. One inbox, one provider, one person, a 20-year-old
  phishing corpus, and public corpora from 2002-2008.

The owner's decision of 2026-11-11 was to allow a personal-mailbox model to be published if it carries no personal
data; F passed that gate, and the user's instruction of 2026-11-12 was to train on the Kaggle corpora, test the
model and push. F is the measured outcome of exactly that.

## 16. How to reproduce

All commands run from `backend/` on Windows PowerShell.

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
python -m pytest -q
```

Build the temporal split. The directories are gitignored and may already exist on the evaluation machine; these
commands rebuild them from the downloaded corpora.

```powershell
New-Item -ItemType Directory -Force ..\.tmp\nazario-train-old, ..\.tmp\nazario-test-2015-2023, ..\.tmp\nazario-test-2024-2025 | Out-Null

Copy-Item data\raw\nazario\phishing0.mbox, data\raw\nazario\phishing1.mbox, data\raw\nazario\phishing2.mbox `
  -Destination ..\.tmp\nazario-train-old

Copy-Item data\raw\nazario\phishing-201*.mbox, data\raw\nazario\phishing-202[0-3].mbox `
  -Destination ..\.tmp\nazario-test-2015-2023

Copy-Item data\raw\nazario\phishing-2024.mbox, data\raw\nazario\phishing-2025.mbox `
  -Destination ..\.tmp\nazario-test-2024-2025
```

Do not copy `20051114.mbox` into the training split; it overlaps the 2005 mboxes and is already deduplicated by the
loader.

Clean baseline:

```powershell
.\.venv\Scripts\python.exe -m training.evaluate_modern `
  --model-dir models `
  --phish-dir ..\.tmp\nazario-test-2015-2023 `
  --phish-since 2015-01-01 --phish-until 2024-01-01 `
  --out reports\modern-holdout
```

Auth-blind diagnostic, once it is ready:

```powershell
.\.venv\Scripts\python.exe ..\.tmp\auth_blind_experiment.py
```

The harness defaults to `models` for `--model-dir` and to
`data/raw/mailbox/All mail Including Spam and Trash.mbox` for `--mailbox`, so those flags can be omitted when
running from `backend/`.

The Kaggle corpora, the candidate that was released, and the shared holdout:

```powershell
.\.venv\Scripts\python.exe -m training.download_kaggle

# F: Nazario pre-2024 + Kaggle phishing on the phishing side, SpamAssassin + Kaggle ham + the
# owner's mailbox on the legitimate side.
$py = ".\.venv\Scripts\python.exe"
$a = @("-u", "-m", "training.train", "--source", "corpus")
$a += @("--phish-dir", "..\.tmp\nazario-train-pre2024", "data\raw\kaggle\ceas08\phishing", "data\raw\kaggle\nigerian-fraud\phishing")
$a += @("--legit-dir", "data\raw\spamassassin", "data\raw\kaggle\ceas08\legitimate", "data\raw\kaggle\spamassassin-kaggle\legitimate")
$a += @("--legit-mailbox", "data/raw/mailbox", "--legit-until", "2026-01-01")
$a += @("--out", "..\.tmp\models-F2", "--reports", "..\.tmp\reports-F2")
& $py @a

# The shared holdout: 2026 messages from the inbox, and the 2024-2025 archives.
& $py -u -m training.evaluate_modern --model "..\.tmp\models-F2\xgboost-corpus-20261112-s7" `
  --mailbox "data/raw/mailbox" --mailbox-since 2026-01-01 `
  --phish-dir "..\.tmp\nazario-holdout-2024-2025" --phish-since 1970-01-01 --phish-until 2039-01-01 `
  --out "..\.tmp\eval-F2"

# The privacy gate, then the release.
& $py -u -m scripts.audit_model --model "..\.tmp\models-F2\xgboost-corpus-20261112-s7" --mailbox "data/raw/mailbox"
& $py -u -m scripts.release_model --model "..\.tmp\models-F2\xgboost-corpus-20261112-s7" `
  --mailbox "data/raw/mailbox" --allow-personal-data --notes "..."
```

The holdout directories are built the same way as the training split above: copy `phishing-2024.mbox` and
`phishing-2025.mbox` into `..\.tmp\nazario-holdout-2024-2025`, and use the owner's mailbox for the legitimate side,
which the loader filters to received messages.

## 17. The source-leak test (2026-11-12)

An external reviewer asked the right question about the released model. The only modern legitimate mail in the
training set is the owner's own inbox, so the features may identify the **provider and the era** rather than the
message being legitimate. If they do, the measured false-positive rate does not transfer to another person's
mailbox.

### 17.1 The test

Take legitimate mail only, from three corpora with different providers and eras, and train a classifier to predict
**which corpus it came from**. If the features carry a source fingerprint, the classifier will do well. Chance is
1/3. 1,500 messages per corpus, a 70/30 split, and the features are the same 65 the phishing model uses.

| corpus | what it is |
|---|---|
| mailbox (2020-2026, owner) | one modern provider, authenticated mail, Gmail Takeout export |
| spamassassin (2003) | pre-authentication-era ham |
| ceas (2008) | pre-authentication-era ham, a different collection pipeline |

### 17.2 The result: the fingerprint is real

| features used | accuracy | chance | verdict |
|---|---|---|---|
| all 65 | **0.981** | 0.333 | the source is recoverable |
| the 13 header/format features only | **0.980** | 0.333 | the fingerprint lives in the headers |

The header group alone is enough. These are the features that carry it:

| feature | mailbox | spamassassin 2003 | ceas 2008 |
|---|---|---|---|
| `received_hops` | 0.134 | 0.330 | 0.000 |
| `from_returnpath_mismatch` | 0.221 | 0.859 | 0.000 |
| `auth_missing` | 0.004 | 1.000 | 1.000 |
| `spf_pass` | 0.991 | 0.000 | 0.000 |
| `dkim_pass` | 0.994 | 0.000 | 0.000 |
| `dmarc_pass` | 0.967 | 0.000 | 0.000 |

These are exactly the differences the reviewer named: a modern authenticated mailbox has a multi-hop `Received`
chain and passing SPF/DKIM/DMARC, while a 2003 corpus or a raw honeypot capture has neither.

### 17.3 Does the released model exploit it?

Only a little, and that is what decides what may be claimed. Gain share in the released model
(`xgboost-corpus-20261112-s7`, XGBoost, 52,333 training rows):

| feature | gain share |
|---|---|
| `subject_reply_without_history` | 41.5% |
| `subject_caps_ratio` | 4.9% |
| `unique_domain_count` | 4.3% |
| `max_path_depth` | 4.2% |
| `financial_terms_ratio` | 4.2% |
| `dmarc_pass` | 3.2% |
| `text_length` | 3.1% |
| `dkim_pass` | 2.7% |
| `requests_click` | 2.7% |

The ten era/provider-fingerprint features together hold **10.1%** of the gain. The dominant signal is content and
behaviour, not the provider. The model is not "recognising my provider and calling it legitimate", but the margin
is not zero either.

### 17.4 What may and may not be claimed

- **May claim:** FPR 0.018 at probability 0.50 on **2,865 held-out 2026 messages from the same inbox** - a temporal
  holdout of mail from the provider the model was trained on.
- **May not claim:** a false-positive rate for email in general, or for another person's mailbox. The 0.018 does
  not measure that, and this repository has no second modern legitimate source to measure it with.
- The fix the reviewer names is the one this project cannot complete on its own: modern legitimate mail from an
  inbox that is not the owner's, and modern phishing on the training side. Nazario 2015-2023 already provides part
  of the latter; the former needs a second contributor's mailbox, which is a data question, not a code question.

### 17.5 Reproducing it

`backend/scripts/source_leak_test.py` (the classifier) and `backend/scripts/released_model_importances.py` (the
gain shares). Both need the gitignored corpora, so they are scripts and not part of the pytest suite.

## 18. Operating points and calibration (2026-11-12)

A reviewer asked for the two numbers a triage tool is judged on, and the harness had neither: recall at a fixed
low false-positive rate, and whether the probabilities mean anything. Both are now produced by
`training.evaluate_modern`, measured on the shared holdout - 2,865 legitimate messages from 2026 that the model
never saw, and 788 phishing messages from the 2024-2025 archives.

### 18.1 Recall at a fixed false-positive rate

The analyst only looks at what the system flags, so the useful question is not "what is the recall at probability
0.5" but "if we only flag 1% of the legitimate mail, how much phishing do we catch".

| False-positive budget | Threshold | False positives | Phishing caught | Recall | Precision |
|---|---|---|---|---|---|
| 1% | 0.722 | 28 of 2,865 | 522 of 788 | **0.662** | 0.949 |
| 5% | 0.203 | 95 of 2,865 | 635 of 788 | **0.806** | 0.870 |

At a 1% budget the analyst sees 28 false alarms in 2,865 legitimate messages, and 94.9% of what is flagged really is
phishing. At 5%, 635 of the 788 phishing messages are caught. Both numbers describe a triage tool better than the
band-boundary recall of 0.770 does.

### 18.2 Calibration: the HIGH band can be trusted, the LOW band cannot

Per risk band, the mean predicted probability against the phishing rate actually observed:

| Band | n | Mean predicted | Observed phishing rate | Phishing messages |
|---|---|---|---|---|
| LOW | 2,987 | 0.025 | **0.061** | 181 |
| MEDIUM | 115 | 0.526 | 0.730 | 84 |
| HIGH | 551 | 0.930 | **0.949** | 523 |

The reliability curve shows the same shape - calibrated at the top, over-confident at the bottom:

| Predicted range | n | Mean predicted | Observed rate |
|---|---|---|---|
| 0.0-0.1 | 2,725 | 0.010 | 0.036 |
| 0.1-0.2 | 198 | 0.179 | 0.283 |
| 0.2-0.3 | 64 | 0.204 | 0.438 |
| 0.5-0.6 | 94 | 0.538 | 0.755 |
| 0.8-0.9 | 50 | 0.847 | 0.860 |
| 0.9-1.0 | 403 | 0.987 | 0.983 |

**What this means for the product.** A HIGH band means what it says: 94.9% of the messages in it really are
phishing. A LOW band does not mean "safe" - the model predicts 2.5% risk there and the truth is 6.1%, and 181 of
the 788 phishing messages land in LOW. The isotonic calibration was fitted on the training distribution, where
legitimate mail is dominated by the 2003 and 2008 corpora and modern phishing by 2015-2023; on a 2026 mix the
bottom of the range is where it drifts.

Two consequences, and both are cheap:
- The UI must not present LOW as "safe". It should state what the number means, which is the honest reading of a
  6% residual risk.
- The calibration curve is what to fix before the probabilities are quoted to an end user. The band boundaries are
  a presentation layer on top of it, and the HIGH band - the one that drives the analyst's attention - is already
  sound.

### 18.3 Reproducing it

```powershell
cd backend
.\.venv\Scripts\python.exe -u -m training.evaluate_modern --model release/model `
  --mailbox "data/raw/mailbox" --mailbox-since 2026-01-01 `
  --phish-dir "..\.tmp\nazario-holdout-2024-2025" --phish-since 1970-01-01 --phish-until 2039-01-01 `
  --out "..\.tmp\eval-release-new"
```

Roughly fifteen minutes: the mailbox is about 370 MB of raw mbox, and every message is parsed and featurised.

## 19. The candidate with the modern phishing corpus (2026-11-12)

The method in `docs/22-training-methodology-and-measurements.md` was applied end to end: a modern phishing corpus,
a temporal split, operating points chosen on validation, and a seed sweep. The candidate is written to
`backend/models-eval/xgboost-corpus-20261112-s7` and is **not activated**; the serving model is untouched.

**The data.** 36,048 messages, 13,546 phishing and 22,502 legitimate, in 11,631 groups. Phishing is Nazario (4,306)
plus Phishing Pot (9,240); legitimate is SpamAssassin easy_ham (2,472) and hard_ham (240), CEAS 2008 legitimate
(17,211) and the owner's mailbox before 2026-01-01 (2,579). The 633 messages from `spamassassin.taint.org` are
excluded, as before.

**The split.** Temporal, by group: fit 26,004, validation 4,019, test 5,392. The test partition is 5,156 phishing and
236 legitimate, because the newest mail in every corpus is phishing: SpamAssassin is from 2003, CEAS from 2008, and
the modern phishing is from 2022 onwards. That is why the false-positive rate cannot be read off the test partition
alone; it comes from the 2026 mailbox holdout, which no partition touches.

**The result on the temporal holdout** (5,156 modern phishing, 236 legitimate):

| metric | value |
|---|---|
| macro F1 | 0.824 |
| phishing F1 | 0.978 |
| precision | 0.998 |
| recall | 0.959 |
| false-positive rate | 0.042 |
| ROC-AUC | 0.985 |
| PR-AUC | 0.999 |
| Brier score | 0.032 |
| confusion (TN, FP, FN, TP) | 226, 10, 213, 4943 |

**The spread.** Three seeds, each a full run: macro F1 **0.819 +/- 0.009**, ROC-AUC **0.984 +/- 0.002**.

**The ablation agrees with the leak test.** Dropping the header group costs the most of any group: macro F1 falls from
0.773 to 0.695 and ROC-AUC from 0.984 to 0.873. The header features carry more of the signal than any other block,
which is the same finding as the corpus-recovery test in section 17, seen from the other side.

**The operating points** came out of the validation set: a 1% false-positive budget needs a score of 100 (recall 0.295,
precision 0.986) and a 5% budget needs 99 (recall 0.826, precision 0.974). Those thresholds sit at the very top of the
0-100 scale because the isotonic calibrator maps almost everything to the extremes, so the usable operating range is
narrow. The bands that ship stay a product decision.

**How this compares with the released model.** Not directly, and the difference matters: the released model was
measured against 788 held-out modern phishing messages with a recall of 0.770, while this candidate is measured on
5,156 modern phishing messages it has never seen and reaches 0.959. Phishing Pot is in the same era and style as the
newest campaigns, so the candidate has the easier holdout. The two numbers are not a before-and-after. The comparable
figure is the false-positive rate on the 2026 mailbox holdout, which both models can be scored on, and that is what
`python -m training.evaluate_modern` measures.

### 19.1 The candidate was measured, and rejected

Scored on the same 2,865 legitimate messages from the 2026 inbox holdout, with the leakage check **clear** on both
sides:

| | released model | candidate | 
|---|---|---|
| false-positive rate at p >= 0.50 | 0.018 | **0.129** |
| false-positive rate at the band boundary | 0.021 | **0.234** |
| domain-macro false-positive rate | 0.068 | **0.472** |
| recall on 2008-era phishing | detects them | **0.000** on 20,830 messages |

The candidate is worse on both counts, so it stays where it is, in the gitignored `backend/models-eval/`, and the
released model keeps serving.

Two causes, and they are worth separating because only one of them is the method's fault:

1. **The corpus composition was wrong.** The candidate's training set contained the 2008 corpus only as *legitimate*
   mail, so the model learned that mail from that corpus is safe, and it scores 20,827 of 20,830 of those phishing
   messages as LOW. The released model had that corpus as phishing as well, and detects it. A corpus that appears in
   training must appear in both classes or it teaches the model that its own era is safe.
2. **A temporal split over corpora from different eras separates the eras.** The fit partition came out 22% phishing,
   because the oldest mail is nearly all legitimate and the newest is nearly all phishing. The model then learns
   "modern-looking is phishing" and the era shortcut gets worse instead of better.

The first is a mistake in the training command and would be fixed by including the 2008 phishing in the candidate's
training set. The second is a property of the method, and it is the same era shortcut the shortcut test measures.
**Adding a modern phishing corpus without a matched modern legitimate corpus makes the model worse, not better.**
The fix is still what the shortcut test says it is: legitimate mail and phishing mail from the same world, and a
second inbox to measure on.

## 20. Related documents


- [17 - Real-corpus evaluation](17-real-corpus-evaluation.md): the grouped-split result and its caveats.
- [18 - Open manual actions](18-open-manual-actions.md): work that needs the user.
- [22 - Training methodology and measurements](22-training-methodology-and-measurements.md): the method, the
  measurements, and what is not tested.
- [19 - Teammate training guide](19-teammate-training-guide.md): the training commands and the era-artifact
  explanation.
- [20 - Model parameters and features](20-model-parameters-and-features.md): the 65 features, candidates,
  calibration, and bands.
- [15 - Risks and limitations](15-risks-and-limitations.md): the honest limit this plan measures.
- [13 - Testing and evaluation](13-testing-and-evaluation.md): the existing harnesses and test suite.
- [Dataset card](datasets/README.md): corpus provenance and split rules.
- [Documentation index](README.md): the full document set.
- [File inventory](FILE_INVENTORY.md): what each tracked path is for.
