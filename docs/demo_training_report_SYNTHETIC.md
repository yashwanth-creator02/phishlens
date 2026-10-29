# Training report

Data source: **synthetic (pipeline check only, NOT a result)**

> WARNING: trained on generated data. These numbers only show that the pipeline runs; they are NOT
> evidence about real phishing. Re-run with real corpora before reporting any result.

Selected model: **xgboost** (`xgboost-synthetic-20261026-s7`), split fit/validation/test = {'fit': 1341, 'validation': 294, 'test': 765}

## Held-out test set (uncalibrated models)

| model | f1_macro | f1_phish | precision | recall | fpr | roc_auc | pr_auc | brier |
|---|---|---|---|---|---|---|---|---|
| logistic_regression | 0.964 | 0.947 | 0.951 | 0.942 | 0.018 | 0.965 | 0.953 | 0.037 |
| random_forest | 0.972 | 0.958 | 0.975 | 0.942 | 0.009 | 0.969 | 0.949 | 0.037 |
| xgboost | 0.959 | 0.939 | 0.946 | 0.933 | 0.020 | 0.963 | 0.947 | 0.033 |
| baseline_url_only_rf | 0.961 | 0.943 | 0.974 | 0.913 | 0.009 | 0.956 | 0.933 | 0.038 |

## Selected model after isotonic calibration (test)

| f1_macro | f1_phish | precision | recall | fpr | roc_auc | pr_auc | brier |
|---|---|---|---|---|---|---|---|
| 0.962 | 0.944 | 0.956 | 0.933 | 0.016 | 0.964 | 0.928 | 0.028 |

Confusion matrix (TN, FP, FN, TP): 548, 9, 14, 194

## Ablation (XGBoost, drop one feature group)

| dropped group | macro F1 | ROC-AUC |
|---|---|---|
| header | 0.941 | 0.967 |
| url | 0.951 | 0.968 |
| text | 0.951 | 0.956 |
| action | 0.941 | 0.960 |
| attachment | 0.960 | 0.962 |
| behaviour | 0.949 | 0.964 |
