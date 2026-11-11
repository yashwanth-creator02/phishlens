# Feature expansion, retrained model, and parameter documentation

Date: 2026-11-10
Scope: request to widen the model input beyond the original 57 features and to document the
features and hyperparameters actually in use.

## What changed

The extractor now emits **65 features** in the same six groups (header, url, text, action,
attachment, behaviour). Eight were added, each computed offline from the parsed message so the
serving path stays deterministic and free of network lookups:

| Group | Feature | Definition | Why |
|---|---|---|---|
| url | `max_path_depth` | Deepest link path, in segments, scaled by 8 | Deep paths are a cheap way to hide a phishing landing page under a believable host |
| url | `has_port` | Any link with an explicit non-80/443, malformed, or out-of-range port | Rare in legitimate mail; a classic obfuscation trick |
| url | `percent_encoding_ratio` | Share of `%XX` escapes in the longest such link | Encoded paths hide redirects and brand names from naive readers |
| text | `subject_caps_ratio` | Uppercase letter share of the subject | Subject shouting is independent of the body caps signal |
| text | `generic_greeting` | Subject/body opens with `Dear customer`-style salutation | Mass phishing cannot address the recipient, real correspondents usually do |
| action | `action_count` | Share of the five request types that fire | Multiple simultaneous asks (click, credentials, payment, download, reply) is stronger than any one |
| attachment | `max_attachment_size` | Largest attachment size, `log1p` scaled at 25 MB | Oversized attachments correlate with droppers and archive bombs |
| behaviour | `subject_reply_without_history` | Subject starts `Re:`/`Fwd:` from a sender with no history | Thread hijacking does not need a real prior thread |

Files: `backend/app/features/{url,text,action,attachment,behavioral}_features.py` and
`lexicons.py`. The ordered registry in `feature_vector.py` derives from the module `NAMES`
lists, so the shared vector, the SHAP background, and the model registry check all moved
together. `test_feature_registry_is_consistent` pins the count at 65.

While reviewing the new URL code, `urlparse(...).port` turned out to raise `ValueError` on a
hostile href such as `https://example.com:99999/x` or `http://example.com:abc/y`. That would
have turned a crafted email into a 500 instead of a scored analysis. The extractor now treats
an unparseable port as suspicious (`has_port = 1`) instead of failing, covered by
`test_url_features_tolerate_malformed_port`.

## Retrained model

`training.train --source corpus` on the same Nazario + SpamAssassin corpora selected XGBoost
again and wrote `xgboost-corpus-20261110-s7` to the gitignored `backend/models/active/`:
4,261 messages, split 2,647 fit / 628 validation / 986 test, isotonic calibration, FPR ceiling
0.03, reason threshold 0.1.

| Metric (calibrated, held-out test) | Value |
|---|---|
| Accuracy | 0.978 |
| Precision | 0.965 |
| Recall | 0.989 |
| F1 (phishing class) | 0.977 |
| F1 macro | 0.978 |
| FPR | 0.033 |
| ROC-AUC | 0.993 |
| PR-AUC | 0.986 |
| Brier | 0.014 |

Confusion matrix TN/FP/FN/TP = 499/17/5/465. Uncalibrated, the same model scores F1 macro
0.987 and PR-AUC 0.999; calibration buys probability honesty at the cost of a little
separation. The 2026-11-06 run on the 57-feature vector scored F1 macro 0.983 and PR-AUC
0.984, so this is **not** a controlled comparison of the feature set - the input changed and
the numbers are close. The per-group ablation in `docs/17-real-corpus-evaluation.md` is the
honest read: dropping header (0.972) or url (0.983) costs the most; the new action and
attachment features add little on these corpora, which contain few executable attachments and
little marketing mail.

## Decisions

- No new reason rules. The eight features influence the score but no `templates.RULES` entry
  references them, so a Medium/High verdict driven by them resolves to the generic fallback
  reason rather than an unsupported specific claim. Documented as a follow-up, not hidden.
- No online lookups were introduced for the new features; domain age remains the only
  provider-backed input and still degrades to `landing_domain_age_missing`.
- The serving model was **not** promoted into the Docker image or Render. The public
  deployment still bakes the synthetic demo model, per the existing manual step in
  `docs/18-open-manual-actions.md`.

## Documentation

New `docs/20-model-parameters-and-features.md` is the canonical list of the 65 features, the
candidate hyperparameters and selection rule, calibration, bands, and reason threshold. Also
updated: `README.md`, `AGENTS.md`, `docs/01`, `03`, `04`, `05`, `07`, `08`, `10`, `13`, `16`,
`17`, `19`, `FILE_INVENTORY.md`, `README.md` (docs index), `docs/report/final-report.md`,
`docs/report/04-methodology-part-2-and-outcomes.md`, and `ADR-004`.

## Verification

- `python -m pytest -q` in `backend/`: 52 passed, 1 skipped (the live-only Supabase RLS test).
- `test_features.py`: 8 passed, including the new malformed-port case.
- Working tree contains no control characters and no stray `\u000B` escapes (scanned every
  tracked text file after an editor glitch while writing the project log).
- Frontend untouched; no rebuild required for this change.

## Follow-ups

- Add reason rules for the new features, or accept the fallback reason for them explicitly.
- Promote the corpus model only after deciding what to do about the `auth_missing` era artefact
  documented in `docs/17-real-corpus-evaluation.md`.
- Re-run the ablation on a corpus with modern attachments and marketing mail before claiming
  the action/attachment groups add value.
