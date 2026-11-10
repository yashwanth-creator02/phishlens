# 13 - Testing and evaluation

## Automated tests (`cd backend && python -m pytest -q`) - 52 passing, 1 skipped
| File | What it proves |
|---|---|
| `test_parser.py` | direct / forward-as-attachment / inline-forward parsing; inline forward marks authentication as **missing**; attachment metadata only |
| `test_features.py` | 65 unique features in 6 groups; phishing sample triggers expected features; legitimate sample is quiet; double-extension attachment; behavioural features need >= 3 history messages and detect new return-path / reply-to / link domain |
| `test_reasons_and_bands.py` | **a reason without evidence is discarded**; reasons use real values; negative contributions never become reasons; behavioural reasons suppressed on cold start; top-k with group diversity; band thresholds; generic fallback |
| `test_api.py` | health; phishing -> MEDIUM/HIGH with verified reasons; legitimate -> LOW; inline forward; list/detail/features/delete; empty upload 400; **auth required and users isolated** (Supabase JWT mode); webhook secret/alias/JSON form; baseline builds history and HIGH risk does not pollute it; model endpoint |
| `test_corpus_loading.py` | extensionless (hash-named) corpus files load; mbox plus loose files produce both classes |
The API tests train a small synthetic model once per session (about 10 s).

### Frontend

| Command | Scope | Result |
|---|---|---|
| `cd frontend; npm test` | Vitest + Testing Library across the API client, cases helpers, shell, login, feature table | 18 tests in 5 files |
| `cd frontend; npm run build` | type-check plus production bundle | passes |
| `cd frontend; npm run test:e2e` | Playwright smoke against a dev server | 1 passed; signed-in journey skips without `E2E_EMAIL` / `E2E_PASSWORD` |

The Playwright suite (`frontend/e2e/smoke.spec.ts`) is deliberately split: an unauthenticated check that runs in both
auth modes, and a signed-in journey (dashboard, cases, model, how-it-works, status, settings, case detail) that needs a
seeded Supabase user. Set `E2E_BASE_URL` to run it against a deployment instead of `localhost:5173`. The vitest
`include` pattern is limited to `src/**`, so Playwright files are never picked up by the unit runner.

### Real-data evaluation harness

`backend/training/evaluate.py` runs the grouped-split experiment: URL host and sender domain are kept inside one fold,
and a random-split baseline is reported alongside for comparison. It writes `reports/evaluation.json` and
`reports/evaluation.md`.

```powershell
cd backend
python -m training.download_datasets                    # Nazario + SpamAssassin, SHA-256 manifests recorded
python -m training.evaluate                             # grouped split -> reports/evaluation.{json,md}
```

Measured result on 4,102 messages (1,390 Nazario phishing, 2,712 SpamAssassin ham), grouped split, 3,092 train /
1,010 test: **F1 0.948, PR-AUC 0.990, precision 0.968, recall 0.930, FPR 0.025**, against a leaky random-split F1
of 0.962. Method, caveats, and the exact reasons those numbers are not production accuracy are in
[17-real-corpus-evaluation.md](17-real-corpus-evaluation.md).

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
