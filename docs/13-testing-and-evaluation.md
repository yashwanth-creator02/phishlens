# 13 - Testing and evaluation

## Automated tests (`cd backend && python -m pytest -q`) - 30 passing
| File | What it proves |
|---|---|
| `test_parser.py` | direct / forward-as-attachment / inline-forward parsing; inline forward marks authentication as **missing**; attachment metadata only |
| `test_features.py` | 57 unique features in 6 groups; phishing sample triggers expected features; legitimate sample is quiet; double-extension attachment; behavioural features need >= 3 history messages and detect new return-path / reply-to / link domain |
| `test_reasons_and_bands.py` | **a reason without evidence is discarded**; reasons use real values; negative contributions never become reasons; behavioural reasons suppressed on cold start; top-k with group diversity; band thresholds; generic fallback |
| `test_api.py` | health; phishing -> MEDIUM/HIGH with verified reasons; legitimate -> LOW; inline forward; list/detail/features/delete; empty upload 400; oversized upload 413; **auth required and users isolated** (Supabase JWT mode); webhook secret/alias/JSON form; oversized webhook body 400; baseline builds history and HIGH risk does not pollute it; model endpoint |
The API tests train a small synthetic model once per session (under a minute on the reference machine). Frontend: `npm run build` type-checks; no component tests yet (add Vitest + Testing Library).

## Evaluation experiments (to run on REAL data)
| ID | Experiment | Purpose |
|---|---|---|
| E1 | proposed models vs the existing-approach baseline on identical splits | Objective 2, model selection |
| E2 | cross-dataset: train on one corpus, test on another | generalisation |
| E3 | temporal split (train earlier, test later) | robustness over time |
| E4 | test on LLM-rewritten / LLM-generated phishing | generative-AI robustness |
| E5 | ablation: drop one feature group at a time (script already in `train.py`) | value of each evidence group |
| E6 | error analysis of false positives / false negatives | Objective 4 |
| E7 | explanation faithfulness (deletion test, stability) + manual audit | Objective 3 |
| E8 | latency per email and per stage | feasibility of synchronous processing |

Measures: accuracy, precision, recall, F1 (macro and phishing), FPR, ROC-AUC, PR-AUC, Brier. Bootstrap 95% CIs; McNemar for paired comparisons.
Error taxonomy: FN - well-written LLM phishing, compromised sender, very short messages, image-only; FP - marketing with shortened links, automated notifications, genuine unfamiliar senders.

## What not to claim
Nothing from the synthetic generator. Nothing about behavioural features beyond what the semi-synthetic benchmark supports. No accuracy figure without the split procedure.
