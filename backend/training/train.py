"""Train, compare, select, calibrate and register a PhishLens model.

    python -m training.train --source synthetic --n 2400 --out models          # pipeline check ONLY
    python -m training.train --source corpus --phish-dir DIR --legit-dir DIR   # real corpora

Outputs <out>/<version_tag>/ and copies it to <out>/active/ (the directory the API serves), plus
reports/training_report.md|json. Metrics on synthetic data are a pipeline sanity check, not results.
"""
from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.model_selection import GroupShuffleSplit
from xgboost import XGBClassifier

from app.features.feature_vector import FEATURE_GROUP, FEATURE_NAMES, GROUPS

from . import corpus, synthetic

REASON_MIN = {"xgboost": 0.10, "logistic_regression": 0.10, "random_forest": 0.02}
FPR_CEILING = 0.03


def metrics(y, p, thr=0.5) -> dict:
    pred = (p >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0), "f1_phish": f1_score(y, pred, zero_division=0),
            "f1_macro": f1_score(y, pred, average="macro"), "fpr": fp / max(1, fp + tn),
            "roc_auc": roc_auc_score(y, p), "pr_auc": average_precision_score(y, p), "brier": brier_score_loss(y, p),
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def make_models(y_fit, seed):
    pos = max(1, int(y_fit.sum()))
    return {
        "logistic_regression": LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced"),
        "random_forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=2,
                                                class_weight="balanced", n_jobs=-1, random_state=seed),
        "xgboost": XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.08, subsample=0.9, colsample_bytree=0.9,
                                 scale_pos_weight=(len(y_fit) - pos) / pos, eval_metric="logloss", n_jobs=2,
                                 random_state=seed, verbosity=0),
    }


def split_groups(groups, test_size, seed):
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    return next(gss.split(np.zeros(len(groups)), groups=groups))


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "corpus"], default="synthetic")
    ap.add_argument("--n", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--phish-dir")
    ap.add_argument("--legit-dir")
    ap.add_argument("--limit", type=int, default=None, help="max emails per class (corpus mode)")
    ap.add_argument("--out", default="models")
    ap.add_argument("--reports", default="reports")
    args = ap.parse_args(argv)
    t0 = time.time()

    if args.source == "synthetic":
        samples = synthetic.build_samples(n=args.n, seed=args.seed)
        data_source = "synthetic (pipeline check only, NOT a result)"
    else:
        samples = corpus.load_dir(args.phish_dir, 1, args.limit) + corpus.load_dir(args.legit_dir, 0, args.limit)
        data_source = f"corpus: phish={args.phish_dir} legit={args.legit_dir}"
    X, y, groups = synthetic.samples_to_matrix(samples)
    print(f"dataset: {len(y)} emails, {int(y.sum())} phishing, {X.shape[1]} features, {len(set(groups))} groups")

    # Corpus hygiene: SpamAssassin rewrites some hostnames to spamassassin.taint.org, which lands 633+ messages in a
    # single sender-domain group that the grouped split puts entirely in one partition, inflating false positives.
    taint = np.array([g == "legit-spamassassin.taint.org" for g in groups])
    if taint.sum() > 0:
        keep = ~taint
        print(f"Excluding {int(taint.sum())} messages with sender domain spamassassin.taint.org (corpus artefact).")
        X, y, groups = X[keep], y[keep], groups[keep]

    rest, test = split_groups(groups, 0.25, args.seed)
    fit_i, val_i = split_groups(groups[rest], 0.2, args.seed)
    fit, val = rest[fit_i], rest[val_i]
    Xf, yf, Xv, yv, Xt, yt = X[fit], y[fit], X[val], y[val], X[test], y[test]

    models = make_models(yf, args.seed)
    results_val, results_test = {}, {}
    for name, m in models.items():
        m.fit(Xf, yf)
        results_val[name] = metrics(yv, m.predict_proba(Xv)[:, 1])
        results_test[name] = metrics(yt, m.predict_proba(Xt)[:, 1])

    # "existing approach" baseline (simplified re-implementation): URL-only random forest
    url_idx = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP[n] == "url"]
    base = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=2, class_weight="balanced",
                                  n_jobs=-1, random_state=args.seed).fit(Xf[:, url_idx], yf)
    results_test["baseline_url_only_rf"] = metrics(yt, base.predict_proba(Xt[:, url_idx])[:, 1])

    # selection on the validation split: best macro F1 subject to FPR ceiling, tie -> ROC-AUC
    ok = {k: v for k, v in results_val.items() if v["fpr"] <= FPR_CEILING} or results_val
    best = max(ok, key=lambda k: (round(ok[k]["f1_macro"], 4), ok[k]["roc_auc"]))
    model = models[best]
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(model.predict_proba(Xv)[:, 1], yv)
    p_test_cal = iso.predict(model.predict_proba(Xt)[:, 1])
    selected_test = metrics(yt, p_test_cal)

    # ablation (XGBoost): drop one feature group at a time
    ablation = {}
    for g in GROUPS:
        keep = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP[n] != g]
        m = make_models(yf, args.seed)["xgboost"].fit(Xf[:, keep], yf)
        mm = metrics(yt, m.predict_proba(Xt[:, keep])[:, 1])
        ablation[g] = {"f1_macro": mm["f1_macro"], "roc_auc": mm["roc_auc"]}

    tag = f"{best}-{args.source}-{datetime.now(UTC).replace(tzinfo=None):%Y%m%d}-s{args.seed}"
    out = Path(args.out) / tag
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "model.joblib")
    joblib.dump(iso, out / "calibrator.joblib")
    np.save(out / "background.npy", Xf[np.random.RandomState(args.seed).choice(len(Xf), min(100, len(Xf)), replace=False)])
    meta = {"version_tag": tag, "algorithm": best, "trained_at": datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
            "feature_names": FEATURE_NAMES, "data_source": data_source, "n_samples": int(len(y)),
            "split": {"fit": len(fit), "validation": len(val), "test": len(test)},
            "reason_min_contribution": REASON_MIN[best], "fpr_ceiling": FPR_CEILING,
            "metrics": {k: float(v) for k, v in selected_test.items() if not k in ("tn", "fp", "fn", "tp")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    active = Path(args.out) / "active"
    if active.exists():
        shutil.rmtree(active)
    shutil.copytree(out, active)

    rep_dir = Path(args.reports)
    rep_dir.mkdir(parents=True, exist_ok=True)
    full = {"meta": meta, "validation": results_val, "test": results_test, "selected_calibrated_test": selected_test,
            "ablation_xgboost": ablation}
    (rep_dir / "training_report.json").write_text(json.dumps(full, indent=2))
    (rep_dir / "training_report.md").write_text(render_report(full, data_source))
    print(f"selected: {best}  (macro F1 on test, calibrated = {selected_test['f1_macro']:.3f})  tag={tag}  [{time.time()-t0:.0f}s]")
    return full


def render_report(full: dict, data_source: str) -> str:
    cols = ["f1_macro", "f1_phish", "precision", "recall", "fpr", "roc_auc", "pr_auc", "brier"]
    lines = ["# Training report", "", f"Data source: **{data_source}**", ""]
    if data_source.startswith("synthetic"):
        lines += ["> WARNING: trained on generated data. These numbers only show that the pipeline runs; they are NOT",
                  "> evidence about real phishing. Re-run with real corpora before reporting any result.", ""]
    lines += [f"Selected model: **{full['meta']['algorithm']}** (`{full['meta']['version_tag']}`), "
              f"split fit/validation/test = {full['meta']['split']}", "", "## Held-out test set (uncalibrated models)", "",
              "| model | " + " | ".join(cols) + " |", "|---|" + "---|" * len(cols)]
    for k, v in full["test"].items():
        lines.append(f"| {k} | " + " | ".join(f"{v[c]:.3f}" for c in cols) + " |")
    s = full["selected_calibrated_test"]
    lines += ["", "## Selected model after isotonic calibration (test)", "",
              "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols), "| " + " | ".join(f"{s[c]:.3f}" for c in cols) + " |",
              "", f"Confusion matrix (TN, FP, FN, TP): {s['tn']}, {s['fp']}, {s['fn']}, {s['tp']}", "",
              "## Ablation (XGBoost, drop one feature group)", "", "| dropped group | macro F1 | ROC-AUC |", "|---|---|---|"]
    for g, v in full["ablation_xgboost"].items():
        lines.append(f"| {g} | {v['f1_macro']:.3f} | {v['roc_auc']:.3f} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
