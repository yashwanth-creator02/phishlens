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

## 2. Features (57, six groups) - `backend/app/features/`
Numeric features are scaled to roughly 0-1 in the extractor so linear models and SHAP behave well. Unavailable evidence gets a *missing* flag.
Wording is one group among six: fluent AI-written phishing passes grammar checks.

| # | Feature | Group | Meaning |
|---|---|---|---|
| 1 | `spf_pass` | header | SPF result is pass |
| 2 | `spf_fail` | header | SPF result is fail/softfail |
| 3 | `dkim_pass` | header | DKIM result is pass |
| 4 | `dkim_fail` | header | DKIM result is fail |
| 5 | `dmarc_pass` | header | DMARC result is pass |
| 6 | `dmarc_fail` | header | DMARC result is fail |
| 7 | `auth_missing` | header | no authentication results available at all (e.g. inline forward) |
| 8 | `from_replyto_mismatch` | header | Reply-To registered domain differs from From domain |
| 9 | `from_returnpath_mismatch` | header | Return-Path domain differs from From domain |
| 10 | `display_name_brand_mismatch` | header | display name names a known brand but the address belongs to another domain |
| 11 | `received_hops` | header | number of Received headers (scaled 0-1) |
| 12 | `sender_domain_age_days` | header | sender domain age, log-scaled (missing -> imputed old) |
| 13 | `sender_domain_age_missing` | header | domain age unavailable |
| 14 | `url_count` | url | number of links (scaled) |
| 15 | `unique_domain_count` | url | distinct destination domains (scaled) |
| 16 | `link_text_mismatch` | url | a link's visible text shows a different domain than its real target |
| 17 | `link_text_mismatch_count` | url | how many such links (scaled) |
| 18 | `ip_in_host` | url | a link points to a numeric IP host |
| 19 | `uses_shortener` | url | a link uses a URL shortener |
| 20 | `punycode` | url | a link host uses xn-- (look-alike characters) |
| 21 | `max_subdomain_depth` | url | deepest subdomain nesting (scaled) |
| 22 | `max_url_length` | url | longest URL (scaled) |
| 23 | `special_char_ratio` | url | share of @ % - _ = & ~ characters in the most unusual URL |
| 24 | `brand_in_subdomain_or_path` | url | brand keyword appears outside the brand's real domain |
| 25 | `suspicious_tld` | url | destination uses a scam-prone TLD |
| 26 | `http_only` | url | a link is not https |
| 27 | `landing_domain_age_days` | url | youngest destination domain age, log-scaled |
| 28 | `landing_domain_age_missing` | url | destination age unavailable |
| 29 | `urgency_score` | text | urgency phrases (0-1) |
| 30 | `threat_score` | text | threat phrases (0-1) |
| 31 | `credential_phrase_flag` | text | phrases asking to verify/confirm/re-enter account details |
| 32 | `financial_terms_ratio` | text | share of money-related words (scaled) |
| 33 | `caps_ratio` | text | share of capital letters |
| 34 | `exclaim_count` | text | exclamation marks (scaled) |
| 35 | `readability_score` | text | Flesch reading ease / 100 |
| 36 | `text_length` | text | log word count (scaled) |
| 37 | `requests_click` | action | asks to click (phrases or generic anchor text) |
| 38 | `requests_credentials` | action | asks for login/account details |
| 39 | `requests_payment` | action | asks for a payment/transfer |
| 40 | `requests_download` | action | asks to open/download a file |
| 41 | `requests_reply_info` | action | asks to reply with personal info |
| 42 | `has_attachment` | attachment | any attachment |
| 43 | `attachment_count` | attachment | number of attachments (scaled) |
| 44 | `risky_extension` | attachment | executable/script type (exe, js, scr, iso, ...) |
| 45 | `double_extension` | attachment | disguised name such as invoice.pdf.exe |
| 46 | `macro_enabled_office` | attachment | docm/xlsm/pptm |
| 47 | `mime_extension_mismatch` | attachment | declared type contradicts the extension |
| 48 | `archive_attachment` | attachment | zip/rar/7z... |
| 49 | `sender_seen_before` | behaviour | sender has trusted history for this user |
| 50 | `prior_message_count` | behaviour | trusted messages seen (scaled) |
| 51 | `days_since_first_seen` | behaviour | age of the history, log-scaled |
| 52 | `new_sending_domain` | behaviour | Return-Path domain never used by this sender |
| 53 | `replyto_changed` | behaviour | Reply-To domain never used by this sender |
| 54 | `new_link_domain` | behaviour | links to a domain this sender never linked to |
| 55 | `urgency_deviation` | behaviour | z-score of urgency vs sender baseline (scaled) |
| 56 | `text_style_distance` | behaviour | cosine distance of text fingerprint from sender centroid |
| 57 | `insufficient_history` | behaviour | too little history: behavioural features are not trusted |

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
