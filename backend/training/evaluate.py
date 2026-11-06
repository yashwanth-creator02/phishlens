"""Evaluate PhishLens models on real corpora with grouped cross-validation/splits.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import accuracy_score, average_precision_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split
from xgboost import XGBClassifier

from . import corpus, synthetic


def metrics(y, p, thr=0.5) -> dict:
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "f1_macro": float(f1_score(y, pred, average="macro")),
        "fpr_at_threshold": float(fp / max(1, fp + tn)),
        "roc_auc": float(roc_auc_score(y, p) if len(np.unique(y)) > 1 else 0.5),
        "pr_auc": float(average_precision_score(y, p) if len(np.unique(y)) > 1 else 0.0),
        "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)
    }


def run_evaluation(phish_dir: Path, ham_dir: Path, out: Path) -> dict:
    phish_samples = corpus.load_dir(phish_dir, 1) if phish_dir and Path(phish_dir).exists() else []
    ham_samples = corpus.load_dir(ham_dir, 0) if ham_dir and Path(ham_dir).exists() else []

    samples = phish_samples + ham_samples
    if not samples:
        raise ValueError(f"No emails found under {phish_dir} or {ham_dir}")

    X, y, groups = synthetic.samples_to_matrix(samples)

    # 1) Grouped split (primary)
    gss = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=7)
    train_idx, test_idx = next(gss.split(X, y, groups=groups))

    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=7, verbosity=0)
    model.fit(X_train, y_train)

    p_test = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else model.predict(X_test)
    test_metrics = metrics(y_test, p_test)

    # Cold start metrics: grouped test groups that were unseen in training
    train_groups = set(groups[train_idx])
    cold_mask = np.array([g not in train_groups for g in groups[test_idx]])
    cold_start_n = int(cold_mask.sum())
    if cold_start_n > 0 and len(np.unique(y_test[cold_mask])) > 1:
        cold_p = p_test[cold_mask]
        cold_y = y_test[cold_mask]
        cold_start_f1 = float(f1_score(cold_y, (cold_p >= 0.5).astype(int), zero_division=0))
    else:
        cold_start_f1 = test_metrics["f1"]

    # 2) Random split (comparison)
    X_r_train, X_r_test, y_r_train, y_r_test = train_test_split(X, y, test_size=0.25, random_state=7, stratify=y)
    rand_model = XGBClassifier(n_estimators=100, max_depth=4, learning_rate=0.1, random_state=7, verbosity=0)
    rand_model.fit(X_r_train, y_r_train)
    p_rand = rand_model.predict_proba(X_r_test)[:, 1] if hasattr(rand_model, "predict_proba") else rand_model.predict(X_r_test)
    rand_metrics = metrics(y_r_test, p_rand)

    report = {
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "precision": test_metrics["precision"],
        "recall": test_metrics["recall"],
        "f1": test_metrics["f1"],
        "pr_auc": test_metrics["pr_auc"],
        "fpr_at_threshold": test_metrics["fpr_at_threshold"],
        "test_positives": int(test_metrics["tp"] + test_metrics["fn"]),
        "confusion": {
            "tn": test_metrics["tn"],
            "fp": test_metrics["fp"],
            "fn": test_metrics["fn"],
            "tp": test_metrics["tp"],
        },
        "cold_start_f1": cold_start_f1,
        "cold_start_n": cold_start_n,
        "split_unit": "campaign_or_sender",
        "random_split_f1": rand_metrics["f1"],
        "random_split_pr_auc": rand_metrics["pr_auc"],
    }

    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "evaluation.json").write_text(json.dumps(report, indent=2))
    md_content = f"""# Evaluation Report

- **Train samples**: {report['n_train']}
- **Test samples**: {report['n_test']}
- **Split unit**: {report['split_unit']} (grouped test groups are unseen / out-of-distribution)
- **F1 Score (Grouped)**: {report['f1']:.3f}
- **Precision**: {report['precision']:.3f}
- **Recall**: {report['recall']:.3f}
- **PR-AUC (Grouped)**: {report['pr_auc']:.3f}
- **FPR at threshold**: {report['fpr_at_threshold']:.3f}
- **Confusion (test)**: TP {report['confusion']['tp']} / FP {report['confusion']['fp']} / FN {report['confusion']['fn']} / TN {report['confusion']['tn']} ({report['test_positives']} phishing in test)
- **Cold-start F1**: {report['cold_start_f1']:.3f} (for {report['cold_start_n']} unseen test group samples)
- **Random Split F1**: {report['random_split_f1']:.3f}
- **Random Split PR-AUC**: {report['random_split_pr_auc']:.3f}
"""
    (out / "evaluation.md").write_text(md_content)

    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--phish-dir", type=Path, default=Path("data/raw/nazario"))
    ap.add_argument("--ham-dir", type=Path, default=Path("data/raw/spamassassin"))
    ap.add_argument("--out", type=Path, default=Path("reports"))
    args = ap.parse_args(argv)
    res = run_evaluation(args.phish_dir, args.ham_dir, args.out)
    print("Evaluation completed:", res)
    return res


if __name__ == "__main__":
    main()
