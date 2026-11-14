# Model parameters and features (v0.2)

This is the canonical reference for what the shipped model actually computes. It is generated from
`backend/app/features/*.py` and `backend/training/train.py`; if the two disagree, the code is right and this
page is stale. Regenerate the feature list with:

```powershell
cd backend
.\.venv\Scripts\python.exe -c "from app.features.feature_vector import FEATURE_NAMES, FEATURE_GROUP; [print(i, n, FEATURE_GROUP[n]) for i, n in enumerate(FEATURE_NAMES, 1)]"
```

As of the `xgboost-corpus-20261110-s7` build there are **65 features in 6 groups**.

## 1. Model selection and training parameters

Training fits three candidate models on the same fit split and picks one on the validation split, never on test.

| Item | Value |
|---|---|
| Candidates | `logistic_regression`, `random_forest`, `xgboost` |
| Selection rule | highest rounded macro-F1 on validation, subject to `fpr <= 0.03`; tie broken by ROC-AUC |
| Fallback | if no candidate meets the FPR ceiling, the best macro-F1 candidate is used anyway |
| FPR ceiling | `0.03` (`FPR_CEILING` in `backend/training/train.py`) |
| Calibration | `IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)` fitted on the validation split |
| SHAP background | 100 rows sampled from the fit split (`models/active/background.npy`, shape `100 x 65`) |
| Random seed | `7` |
| Split unit | campaign URL host for phishing, sender domain for ham (`GroupShuffleSplit`) |
| Split sizes | fit 60% / validation 15% / test 25% of the grouped dataset |
| Corpus exclusions | messages whose sender domain is `spamassassin.taint.org` (633 messages) |

### Candidate hyperparameters

Logistic regression:

| Parameter | Value |
|---|---|
| `max_iter` | 2000 |
| `C` | 1.0 |
| `class_weight` | `balanced` |

Random forest:

| Parameter | Value |
|---|---|
| `n_estimators` | 300 |
| `max_depth` | 12 |
| `min_samples_leaf` | 2 |
| `class_weight` | `balanced` |
| `n_jobs` | -1 |
| `random_state` | seed |

XGBoost:

| Parameter | Value |
|---|---|
| `n_estimators` | 300 |
| `max_depth` | 4 |
| `learning_rate` | 0.08 |
| `subsample` | 0.9 |
| `colsample_bytree` | 0.9 |
| `scale_pos_weight` | `(n_negative / n_positive)` of the fit split, ~0.83 on the current corpora |
| `objective` | `binary:logistic` (library default) |
| `eval_metric` | `logloss` |
| `n_jobs` | 2 |
| `random_state` | seed |
| `verbosity` | 0 |

The currently active artifact is `xgboost-corpus-20261110-s7`. Its calibrated held-out metrics are recorded in
`backend/models/active/meta.json` and are not reproduced here because they change on every retrain.

## 2. Scoring and decision parameters

| Item | Value |
|---|---|
| Score | calibrated probability `x 100`, rounded to an integer 0-100 |
| LOW band | score `<= 29` (`band_low_max`) |
| MEDIUM band | score `30-69` |
| HIGH band | score `>= 70` (`band_high_min`) |
| Reason minimum contribution | `0.10` for XGBoost and logistic regression, `0.02` for random forest (`REASON_MIN`) |
| Reason evidence rule | a reason is shown only when its claim verifies against the parsed email; otherwise the generic fallback reason is used |
| Sender history minimum | 3 trusted messages before behavioural deviations are trusted (`min_history`) |
| Sender history update | only LOW-risk analyses; text centroid EMA `alpha = 0.2`; style vector 128 hash buckets over char trigrams |
| Urgency z-score | `|x - mean| / max(stdev, 0.15)` |
| Link-domain cap in history | 200 domains per sender |

## 3. Feature vector (65, in model order)

All values are scaled to roughly 0-1. Features that depend on an external source that is unavailable (domain age,
sender history) set their companion `*_missing` / `insufficient_history` flag rather than inventing a value.

### Header - 13

| # | Feature | Meaning |
|---|---|---|
| 1 | `spf_pass` | SPF result is `pass` |
| 2 | `spf_fail` | SPF result is `fail` |
| 3 | `dkim_pass` | DKIM result is `pass` |
| 4 | `dkim_fail` | DKIM result is `fail` |
| 5 | `dmarc_pass` | DMARC result is `pass` |
| 6 | `dmarc_fail` | DMARC result is `fail` |
| 7 | `auth_missing` | all three authentication results are absent (e.g. inline forward) |
| 8 | `from_replyto_mismatch` | Reply-To registered domain differs from the From registered domain |
| 9 | `from_returnpath_mismatch` | Return-Path registered domain differs from the From registered domain |
| 10 | `display_name_brand_mismatch` | the display name names a known brand but the From domain is not that brand |
| 11 | `received_hops` | Received header count, capped at 20, divided by 20 |
| 12 | `sender_domain_age_days` | log-scaled age of the From registered domain (10 years ~ 1.0); imputed as 1000 days when unknown |
| 13 | `sender_domain_age_missing` | no domain-age provider returned an age for the From domain |

### URL - 18

| # | Feature | Meaning |
|---|---|---|
| 14 | `url_count` | link count, capped at 20, divided by 20 |
| 15 | `unique_domain_count` | distinct registered link domains, capped at 10, divided by 10 |
| 16 | `link_text_mismatch` | some anchor text shows a registered domain different from the real destination |
| 17 | `link_text_mismatch_count` | number of such mismatches, capped at 5, divided by 5 |
| 18 | `ip_in_host` | a link host is a raw IPv4, hex IP, or bracketed IPv6 address |
| 19 | `uses_shortener` | a link domain is in the URL-shortener list |
| 20 | `punycode` | a link host contains `xn--` |
| 21 | `max_subdomain_depth` | deepest subdomain label count, capped at 6, divided by 6 |
| 22 | `max_url_length` | longest href, capped at 300 characters, divided by 300 |
| 23 | `max_path_depth` | deepest URL path segment count, capped at 8, divided by 8 |
| 24 | `has_port` | a link specifies an explicit port other than 80 or 443 |
| 25 | `percent_encoding_ratio` | share of `%XX` octets in the most heavily encoded href |
| 26 | `special_char_ratio` | share of `@ % - _ = & ~` in the most unusual href |
| 27 | `brand_in_subdomain_or_path` | a brand keyword appears in the subdomain or path of a domain the brand does not own |
| 28 | `suspicious_tld` | a link registered domain ends in a scam-prone TLD |
| 29 | `http_only` | a link uses plain `http://` |
| 30 | `landing_domain_age_days` | log-scaled age of the youngest of the first five link domains |
| 31 | `landing_domain_age_missing` | no link domain age was available |

### Text - 10

| # | Feature | Meaning |
|---|---|---|
| 32 | `urgency_score` | urgency phrase hits, capped at 3, divided by 3 |
| 33 | `threat_score` | threat phrase hits, capped at 3, divided by 3 |
| 34 | `credential_phrase_flag` | any verify/confirm/re-enter account phrasing |
| 35 | `financial_terms_ratio` | money-term count over word count, times 10, capped at 1 |
| 36 | `caps_ratio` | share of uppercase letters in subject and body |
| 37 | `subject_caps_ratio` | share of uppercase letters in the subject only |
| 38 | `exclaim_count` | exclamation marks, capped at 10, divided by 10 |
| 39 | `readability_score` | Flesch reading ease, divided by 100 |
| 40 | `text_length` | `log1p(word count) / 8`, capped at 1 |
| 41 | `generic_greeting` | impersonal salutation such as "Dear customer" or "Dear user" |

### Action - 6

| # | Feature | Meaning |
|---|---|---|
| 42 | `requests_click` | a click phrase or a generic anchor such as "click here" |
| 43 | `requests_credentials` | asks for login or account details |
| 44 | `requests_payment` | asks for a payment or transfer |
| 45 | `requests_download` | asks to open or download a file |
| 46 | `requests_reply_info` | asks the reader to reply with personal information |
| 47 | `action_count` | number of distinct action categories present, divided by 5 |

### Attachment - 8

Attachment contents are never opened, rendered, or executed; only metadata is inspected.

| # | Feature | Meaning |
|---|---|---|
| 48 | `has_attachment` | the message has at least one attachment |
| 49 | `attachment_count` | attachment count, capped at 5, divided by 5 |
| 50 | `risky_extension` | an executable or script extension (exe, js, scr, iso, ...) |
| 51 | `double_extension` | a disguised name such as `invoice.pdf.exe` |
| 52 | `macro_enabled_office` | a macro-enabled Office format (docm, xlsm, pptm, ...) |
| 53 | `mime_extension_mismatch` | the declared content type contradicts the extension |
| 54 | `archive_attachment` | zip, rar, 7z, and similar containers |
| 55 | `max_attachment_size` | `log1p(largest attachment bytes) / log1p(25 MB)`, capped at 1 |

### Behaviour - 10

Computed against the per-(user, sender) history of trusted messages. Below three trusted messages the deviation
features are zero and `insufficient_history` is 1.

| # | Feature | Meaning |
|---|---|---|
| 56 | `sender_seen_before` | this sender has trusted history for this user |
| 57 | `prior_message_count` | trusted messages seen, capped at 50, divided by 50 |
| 58 | `days_since_first_seen` | log-scaled age of the sender history |
| 59 | `new_sending_domain` | Return-Path domain never used by this sender |
| 60 | `replyto_changed` | Reply-To domain never used by this sender |
| 61 | `new_link_domain` | links to a domain this sender never linked to |
| 62 | `urgency_deviation` | `|z-score|` of urgency against the sender baseline, capped at 10, divided by 10 |
| 63 | `text_style_distance` | cosine distance from the sender's 128-bucket character-trigram centroid |
| 64 | `subject_reply_without_history` | the subject starts with Re:/Fwd:/Aw:/Sv: but the sender history is below the minimum |
| 65 | `insufficient_history` | fewer than three trusted messages: behavioural features are not trusted |

## 4. What the new v0.2 features do and do not buy

Eight features were added over the v0.1 set of 57: `max_path_depth`, `has_port`, `percent_encoding_ratio`,
`subject_caps_ratio`, `generic_greeting`, `action_count`, `max_attachment_size`, and
`subject_reply_without_history`.

Measured effect on the real-corpus grouped split: the standalone comparator (`training/evaluate.py`, trains on
3,275 and tests on 986) moved from F1 0.987 / PR-AUC 0.998 / FPR 0.012 on the 57-feature vector to F1 0.987 /
PR-AUC 0.999 / FPR 0.012 on 65. The promoted `training.train` run (fit 2,647 / validation 628 / test 986) scores
F1 macro 0.978 and PR-AUC 0.986 after isotonic calibration; that is not comparable to the comparator because it
withholds a validation slice and calibrates.

There is no controlled 57-vs-65 ablation, and the two runs differ in feature set (and, for the promoted model, in
training size). The honest statement is that the added features did not visibly change the headline numbers, not
that they improved or degraded them. They are included because they are cheap, non-redundant, and cover modern URL
obfuscation and thread-hijacking patterns that the 2003-2007 corpora barely exercise.

**The corpus model these parameters describe is not fit for modern mail.** Measured against 2,216 received messages
from a real 2020-2026 inbox, it flags 99.9% of legitimate mail as phishing, and removing the era-sensitive header
features does not fix it. The parameters are still the right description of what the model does; they are not
evidence that the model works on today's mail. See
[21](21-modern-corpus-evaluation-plan.md).

The per-group ablation in `training_report.md` supports the same reading: dropping `header` costs about 1.5 F1
points and dropping `url` about 0.4, while dropping `action` or `attachment` lands within noise of the 0.987
baseline. Treat the feature set as a hypothesis, not a guarantee: re-run
`python -m training.evaluate --out reports` after any change and compare grouped F1, FPR, and PR-AUC before
promoting a model.

## 5. Related pages

- `docs/08-ml-pipeline.md` - pipeline stages, training scripts, and evaluation design.
- `docs/17-real-corpus-evaluation.md` - the measured benchmark and its artefacts.
- `docs/21-modern-corpus-evaluation-plan.md` - modern evaluation and training methodology.
- `docs/15-risks-and-limitations.md` - why the corpora-trained model is not a production detector.
