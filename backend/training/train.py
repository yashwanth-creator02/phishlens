"""Train, compare, select, calibrate and register a PhishLens model.

    python -m training.train --source synthetic --n 2400 --out models --activate          # pipeline check ONLY
    python -m training.train --source corpus --phish-dir DIR --legit-dir DIR --activate   # real corpora

Outputs <out>/<version_tag>/ and, only with --activate, copies it to <out>/active/ (the directory the
API serves), plus reports/training_report.md|json. Without --activate the model stays a candidate so
an offline run can never replace the serving model. Metrics on synthetic data are a pipeline sanity
check, not results.
"""
from __future__ import annotations

import argparse
import hashlib
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


def split_temporal(groups, dates, test_size=0.25, val_size=0.2):
    """Split by time: the oldest mail fits, a later slice validates, the newest tests.

    A group is placed by its EARLIEST date, so a campaign that spans years never
    straddles a boundary - the whole campaign lands on one side of it. Groups
    with no usable date go to the fit split (earliest is None sorted first):
    with no date they cannot be the newest mail in the corpus, and leaving them
    out of the test set is the conservative choice.
    """
    groups = np.asarray(groups)
    dates = np.asarray(dates, dtype=object)
    order = []
    for g in sorted(set(groups.tolist())):
        mask = groups == g
        ds = [d for d in dates[mask].tolist() if d is not None]
        earliest = min(ds) if ds else None
        # Sort undated (earliest is None) first: tuple (True, ...) sorts before (False, ...)
        # Wait: tuple (is_none, date) where is_none=True comes AFTER False unless inverted.
        # We want undated to come first (fit), so key (earliest is None) should be 0 for None, 1 for dated.
        # Let's use: is_none = 0 if earliest is None else 1.
        is_none = 0 if earliest is None else 1
        order.append((is_none, earliest or datetime.min.replace(tzinfo=UTC), g))
    order.sort(key=lambda t: (t[0], t[1], t[2]))

    n = len(order)
    n_test = max(1, int(n * test_size))
    n_val = max(1, int(n * val_size))
    test_groups = {g for _, _, g in order[-n_test:]}
    val_groups = {g for _, _, g in order[-(n_test + n_val):-n_test]}
    fit_groups = {g for _, _, g in order[:-(n_test + n_val)]}

    idx = np.arange(len(groups))
    test = idx[np.isin(groups, list(test_groups))]
    val = idx[np.isin(groups, list(val_groups))]
    fit = idx[np.isin(groups, list(fit_groups))]
    if not len(fit) or not len(val) or not len(test):
        raise SystemExit("the temporal split produced an empty partition; "
                         "there is not enough dated mail to split by time")
    return fit, val, test


def operating_points(y, p, fpr_targets=(0.01, 0.05), calibrator=None) -> dict:
    """The thresholds that hold the false-positive rate inside a budget.

    These are chosen on VALIDATION data and never on the test set. The bands
    are then a presentation layer on top: HIGH above the 1% threshold, MEDIUM
    between the two, LOW below the 5% one.
    """
    from sklearn.metrics import roc_curve

    y = np.asarray(y)
    p = np.asarray(p)
    if len(set(y.tolist())) < 2:
        return {}
    fpr, tpr, thr = roc_curve(y, p)
    out = {}
    for target in fpr_targets:
        ok = np.where(fpr <= target)[0]
        if not len(ok):
            continue
        i = ok[-1]
        threshold = float(thr[i])
        if not np.isfinite(threshold):
            continue
        cal_threshold = threshold
        if calibrator is not None:
            try:
                cal_threshold = float(calibrator.predict([threshold])[0])
            except Exception:
                pass
        flagged_ham = int(np.sum(p[y == 0] >= threshold))
        flagged_phish = int(np.sum(p[y == 1] >= threshold))
        negatives = int(np.sum(y == 0))
        positives = int(np.sum(y == 1))
        out[f"fpr_{target:g}"] = {
            "threshold": threshold,
            "calibrated_threshold": cal_threshold,
            "score_threshold": int(round(cal_threshold * 100)),
            "fpr": float(flagged_ham / max(1, negatives)),
            "recall": float(flagged_phish / max(1, positives)),
            "precision": float(flagged_phish / max(1, flagged_phish + flagged_ham)),
        }
    if "fpr_0.01" in out and "fpr_0.05" in out:
        high_min = int(np.ceil(out["fpr_0.01"]["calibrated_threshold"] * 100))
        low_max = int(np.floor(out["fpr_0.05"]["calibrated_threshold"] * 100))
        if low_max >= high_min:
            low_max = high_min - 1
        out["recommended_bands"] = {"low_max": low_max, "high_min": high_min}
    return out


def fit_and_evaluate(X, y, groups, dates, seed: int, split_mode: str) -> dict:
    """Fit every candidate, pick one on validation, calibrate it, measure it.

    Returns the fitted model, the calibrator, the partitions and the numbers, so
    that the same pipeline can be run again with another seed and the two can be
    compared.
    """
    if split_mode == "temporal":
        fit, val, test = split_temporal(groups, dates)
    else:
        rest, test = split_groups(groups, 0.25, seed)
        fit_i, val_i = split_groups(groups[rest], 0.2, seed)
        fit, val = rest[fit_i], rest[val_i]

    Xf, yf, Xv, yv, Xt, yt = X[fit], y[fit], X[val], y[val], X[test], y[test]
    models = make_models(yf, seed)
    results_val, results_test = {}, {}
    for name, m in models.items():
        m.fit(Xf, yf)
        results_val[name] = metrics(yv, m.predict_proba(Xv)[:, 1])
        results_test[name] = metrics(yt, m.predict_proba(Xt)[:, 1])

    # selection on the validation split: best macro F1 subject to FPR ceiling, tie -> ROC-AUC
    ok = {k: v for k, v in results_val.items() if v["fpr"] <= FPR_CEILING} or results_val
    best = max(ok, key=lambda k: (round(ok[k]["f1_macro"], 4), ok[k]["roc_auc"]))
    model = models[best]
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0).fit(model.predict_proba(Xv)[:, 1], yv)
    p_test_cal = iso.predict(model.predict_proba(Xt)[:, 1])
    selected_test = metrics(yt, p_test_cal)
    # The operating point is chosen on validation, on the RAW probabilities: the calibrator is
    # monotone, so it does not change the ranking, and a threshold taken from calibrated
    # validation scores would be fitted on the very data it is measured against.
    ops = operating_points(yv, model.predict_proba(Xv)[:, 1], calibrator=iso)
    return {"fit": fit, "val": val, "test": test, "models": models, "model": model, "iso": iso,
            "best": best, "results_val": results_val, "results_test": results_test,
            "selected_test": selected_test, "operating_points": ops,
            "X": (Xf, yf, Xv, yv, Xt, yt)}


def check_activation_allowed(provenance: dict, allow_personal_data: bool) -> None:
    """Refuse to promote a model derived from personal mail unless it is explicitly acknowledged."""
    if provenance.get("contains_personal_data") and not allow_personal_data:
        raise SystemExit(
            "Refusing to promote: this model was trained on personal mail, so it is derived from private data. "
            "Keep it local and never bake it into an image. Pass --allow-personal-data if that is what you want "
            "(the model then stays local and out of any public deployment).")


def activate(candidate: Path, active: Path) -> None:
    """Swap a candidate model into place without ever leaving the serving model missing.

    The copy lands in active.new first, the previous model moves to active.prev, and only then is
    active.new renamed to active. If either step fails, the previous model is put back, so a failed
    promotion leaves the service with the model it already had.
    """
    active = Path(active)
    staging = active.with_name(active.name + ".new")
    previous = active.with_name(active.name + ".prev")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(candidate, staging)
    if active.exists():
        if previous.exists():
            shutil.rmtree(previous)
        active.rename(previous)
    try:
        staging.rename(active)
    except Exception:
        if previous.exists():
            previous.rename(active)
        raise


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["synthetic", "corpus"], default="synthetic")
    ap.add_argument("--n", type=int, default=2400)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--phish-dir", nargs="+", required=False,
                    help="phishing corpus directories. More than one is allowed when the corpora "
                         "are disjoint, for example a research archive plus a Kaggle corpus")
    ap.add_argument("--legit-dir", nargs="+", required=False,
                    help="legitimate corpus directories. More than one is allowed when the corpora "
                         "are disjoint")
    ap.add_argument("--legit-mailbox", default=None,
                    help="additional legitimate source: a Gmail Takeout mbox file or a directory of them. "
                         "Personal data: the resulting model is derived from it and must not be published")
    ap.add_argument("--legit-until", default=None,
                    help="keep only mailbox messages dated before this ISO date, so later ones stay a holdout")
    ap.add_argument("--phish-until", default=None,
                    help="drop phishing dated on/after this ISO date (and undated phishing) so a later "
                         "window can be held out for generalization testing")
    ap.add_argument("--activate", action="store_true",
                    help="promote the trained model to <out>/active (the directory the API serves)")
    ap.add_argument("--allow-personal-data", action="store_true",
                    help="allow promoting a model trained on personal mail. Such a model is derived from "
                         "private data: keep it local, never commit it, never bake it into an image")
    ap.add_argument("--limit", type=int, default=None, help="max emails per class (corpus mode)")
    ap.add_argument("--split", choices=["grouped", "temporal"], default="grouped",
                    help="grouped = random over groups; temporal = oldest fit, later validation, newest test")
    ap.add_argument("--seeds", default=None,
                    help="comma separated seeds to sweep, e.g. 7,8,9. The first one is the published candidate")
    ap.add_argument("--out", default="models")
    ap.add_argument("--reports", default="reports")
    args = ap.parse_args(argv)
    t0 = time.time()

    phish_dirs = [Path(d) for d in (args.phish_dir or [])]
    legit_dirs = [Path(d) for d in (args.legit_dir or [])]
    provenance = {"phish_dir": "+".join(corpus.source_label(d) for d in phish_dirs) if phish_dirs else None,
                  "legit_dir": "+".join(corpus.source_label(d) for d in legit_dirs) if legit_dirs else None,
                  "phish_until": args.phish_until,
                  "phish_min_date": None, "phish_max_date": None, "legit_min_date": None, "legit_max_date": None,
                  "phish_undated_dropped": 0, "n_phish": 0, "n_legit": 0,
                  "legit_until": args.legit_until,
                  "legit_mailbox_min_date": None, "legit_mailbox_max_date": None,
                  "n_legit_mailbox": 0, "contains_personal_data": False}
    personal = None
    if args.source == "synthetic":
        samples = synthetic.build_samples(n=args.n, seed=args.seed)
        data_source = "synthetic (pipeline check only, NOT a result)"
    else:
        if not phish_dirs or not (legit_dirs or args.legit_mailbox):
            raise SystemExit("corpus mode needs --phish-dir and at least one of --legit-dir / --legit-mailbox")
        # The date cutoff is applied before --limit: Nazario is stored as per-year archives, so a limit
        # taken first would keep only the oldest years and the cutoff would have no effect.
        phish_stats: dict = {}
        legit_stats: dict = {}
        mailbox_stats: dict = {}
        phish = []
        for d in phish_dirs:
            part = corpus.load_dir(d, 1, stats=phish_stats)
            print(f"phishing corpus {d.name}: {len(part)} messages")
            phish.extend(part)
        legit = []
        for d in legit_dirs:
            part = corpus.load_dir(d, 0, stats=legit_stats)
            print(f"legitimate corpus {d.name}: {len(part)} messages")
            legit.extend(part)
        mailbox = []
        if args.legit_mailbox:
            mailbox = corpus.load_mailbox(args.legit_mailbox, label=0, stats=mailbox_stats)
            if args.legit_until:
                until = corpus.parse_cli_date(args.legit_until)
                kept, late, undated = [], 0, 0
                for s in mailbox:
                    d = corpus.parse_date(s.date)
                    if d is None:
                        undated += 1
                    elif d >= until:
                        late += 1
                    else:
                        kept.append(s)
                print(f"mailbox cutoff {args.legit_until}: kept {len(kept)}, dropped {late} dated on/after the "
                      f"cutoff and {undated} undated messages")
                mailbox = kept
            if args.limit:
                mailbox = mailbox[:args.limit]
            print(f"mailbox legitimate messages used for training: {len(mailbox)} "
                  f"(personal data: the model derived from it must not be published)")
            provenance["n_legit_mailbox"] = len(mailbox)
            provenance["legit_mailbox_min_date"] = corpus.date_range(mailbox)["min"]
            provenance["legit_mailbox_max_date"] = corpus.date_range(mailbox)["max"]
            # The flag follows the data that was actually loaded, not the flag that was passed.
            provenance["contains_personal_data"] = len(mailbox) > 0
        if args.phish_until:
            until = corpus.parse_cli_date(args.phish_until)
            kept, late, undated = [], 0, 0
            for s in phish:
                d = corpus.parse_date(s.date)
                if d is None:
                    undated += 1
                elif d >= until:
                    late += 1
                else:
                    kept.append(s)
            print(f"phish cutoff {args.phish_until}: dropped {late} dated on/after the cutoff and "
                  f"{undated} undated messages")
            provenance["phish_undated_dropped"] = undated
            phish = kept
        if args.limit:
            phish = phish[:args.limit]
            legit = legit[:args.limit]
        if not phish:
            raise SystemExit("no phishing messages left after the date cutoff and --limit")
        if not legit and not mailbox:
            raise SystemExit("no legitimate messages left after the date cutoff and --limit")
        samples = phish + legit + mailbox
        # Which corpus each message came from, so the report can say how much of the model came
        # from where. A corpus that contributes a small share cannot carry the model.
        source_counts: dict[str, int] = {}
        for s in samples:
            key = s.source or "unknown"
            source_counts[key] = source_counts.get(key, 0) + 1
        provenance["source_counts"] = source_counts
        # Rows that came from personal mail. Used to keep personal-derived vectors out of the
        # published artifacts (the SHAP background sample) and out of the served metadata.
        personal = np.array([False] * (len(phish) + len(legit)) + [True] * len(mailbox))
        # Only the directory names go into the artifact: a full path can carry the local account
        # name into a published model file.
        data_source = (f"corpus: phish={provenance['phish_dir']} "
                       f"legit={provenance['legit_dir'] if provenance['legit_dir'] else 'personal mailbox'}")
        provenance["n_phish"] = len(phish)
        provenance["n_legit"] = len(legit)
        provenance["loader_drops"] = {"phish": phish_stats, "legit": legit_stats, "mailbox": mailbox_stats}
        # The phishing split is by archive file, not by message date: the corpus dates are unreliable
        # (some archives carry dates from 1970 to 2038), so the file list is what proves a holdout.
        # Each source is recorded by its label, its size, and a digest of its file names. A corpus
        # of one message per file has tens of thousands of names, and listing them all would make
        # the artifact larger than the model. The archive names are listed in full, because a
        # holdout is made of archives and that is what the leakage guard compares.
        provenance["phish_sources"] = [
            {"label": corpus.source_label(d),
             "count": len(files),
             "name_digest": corpus.name_digest(files),
             "archives": [f for f in files if f.lower().endswith(".mbox")]}
            for d in phish_dirs
            for files in [corpus.source_files(d)]
        ]
        provenance["phish_files"] = [f"{s['label']}/{a}" for s in provenance["phish_sources"]
                                     for a in s["archives"]]
        # The mailbox is personal data, so only a non-reversible digest of its location is recorded.
        # An absolute path would carry the local account name into a published artifact.
        mailbox_path = Path(args.legit_mailbox)
        provenance["legit_mailbox_id"] = corpus.path_digest(mailbox_path)
        provenance["legit_mailbox_scope"] = "directory" if mailbox_path.is_dir() else "file"
        # The file name is not recorded: a Takeout export is named after the account, so even the
        # base name would carry an identifier into a published artifact.
        # A --legit-dir that points at a mailbox export loads the same personal data, so it is
        # flagged the same way.
        if any(d.rglob("*.mbox") for d in legit_dirs):
            provenance["contains_personal_data"] = True
        provenance.update({
            "phish_min_date": corpus.date_range(phish)["min"],
            "phish_max_date": corpus.date_range(phish)["max"],
            "legit_min_date": corpus.date_range(legit)["min"],
            "legit_max_date": corpus.date_range(legit)["max"],
        })
    X, y, groups = synthetic.samples_to_matrix(samples)
    # The date of each message, for the temporal split. A message with no usable date is None
    # and the temporal split puts it in the fit partition rather than in the test set.
    dates = [corpus.parse_date(s.date) for s in samples]
    print(f"dataset: {len(y)} emails, {int(y.sum())} phishing, {X.shape[1]} features, {len(set(groups))} groups")

    # Corpus hygiene: SpamAssassin rewrites some hostnames to spamassassin.taint.org, which lands 633+ messages in a
    # single sender-domain group that the grouped split puts entirely in one partition, inflating false positives.
    taint = np.array([g == "legit-spamassassin.taint.org" for g in groups])
    if taint.sum() > 0:
        keep = ~taint
        print(f"Excluding {int(taint.sum())} messages with sender domain spamassassin.taint.org (corpus artefact).")
        X, y, groups = X[keep], y[keep], groups[keep]
        dates = [d for d, k in zip(dates, keep) if k]
        if personal is not None:
            personal = personal[keep]
    provenance["n_dropped_taint"] = int(taint.sum())
    provenance["n_samples_after_filter"] = int(len(y))

    # A seed sweep repeats the whole pipeline with several seeds, so the spread of the
    # result is known instead of one number from one split.
    seeds = [int(s) for s in (args.seeds or str(args.seed)).split(",") if s.strip()]
    runs = []
    for seed in seeds:
        run = fit_and_evaluate(X, y, groups, dates, seed, args.split)
        runs.append(run)
        print(f"  seed {seed}: {run['best']}  test macro F1 {run['selected_test']['f1_macro']:.3f}  "
              f"ROC-AUC {run['selected_test']['roc_auc']:.3f}")
    sweep = None
    if len(runs) > 1:
        f1s = [r["selected_test"]["f1_macro"] for r in runs]
        aucs = [r["selected_test"]["roc_auc"] for r in runs]
        fprs = [r["selected_test"]["fpr"] for r in runs]
        sweep = {"seeds": seeds,
                 "f1_macro": {"mean": float(np.mean(f1s)), "spread": float(np.max(f1s) - np.min(f1s)),
                              "values": f1s},
                 "roc_auc": {"mean": float(np.mean(aucs)), "spread": float(np.max(aucs) - np.min(aucs)),
                             "values": aucs},
                 "fpr": {"mean": float(np.mean(fprs)), "spread": float(np.max(fprs) - np.min(fprs)),
                         "values": fprs}}
        print(f"  seed spread: F1 {sweep['f1_macro']['mean']:.3f} "
              f"(+/- {sweep['f1_macro']['spread']:.3f}), ROC-AUC {sweep['roc_auc']['mean']:.3f} "
              f"(+/- {sweep['roc_auc']['spread']:.3f})")

    # The candidate that is published is the first seed, so that a sweep is reproducible.
    chosen = runs[0]
    fit, val, test = chosen["fit"], chosen["val"], chosen["test"]
    Xf, yf, Xv, yv, Xt, yt = chosen["X"]
    model, iso, best = chosen["model"], chosen["iso"], chosen["best"]
    results_val, results_test = chosen["results_val"], chosen["results_test"]
    selected_test = chosen["selected_test"]
    ops = chosen["operating_points"]
    provenance["split_mode"] = args.split
    provenance["seeds"] = seeds
    for name, idx in (("fit", fit), ("validation", val), ("test", test)):
        if len(idx):
            ph = int(y[idx].sum())
            print(f"  {name}: {len(idx)} messages, {ph} phishing, {len(idx) - ph} legitimate")
    if ops:
        print(f"operating points on validation: " + ", ".join(
            f"FPR<={k.split('_')[1]}: threshold {v['score_threshold']} "
            f"(recall {v['recall']:.3f}, precision {v['precision']:.3f})"
            for k, v in ops.items() if k.startswith("fpr_")))
        if "recommended_bands" in ops:
            b = ops["recommended_bands"]
            print(f"recommended bands from validation: LOW <= {b['low_max']}, HIGH >= {b['high_min']} "
                  f"(the shipped bands are a product decision; see docs/21)")

    # "existing approach" baseline (simplified re-implementation): URL-only random forest
    url_idx = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP[n] == "url"]
    base = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=2, class_weight="balanced",
                                  n_jobs=-1, random_state=args.seed).fit(Xf[:, url_idx], yf)
    results_test["baseline_url_only_rf"] = metrics(yt, base.predict_proba(Xt[:, url_idx])[:, 1])

    # ablation (XGBoost): drop one feature group at a time
    ablation = {}
    for g in GROUPS:
        keep = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP[n] != g]
        m = make_models(yf, args.seed)["xgboost"].fit(Xf[:, keep], yf)
        mm = metrics(yt, m.predict_proba(Xt[:, keep])[:, 1])
        ablation[g] = {"f1_macro": mm["f1_macro"], "roc_auc": mm["roc_auc"]}

    tag = f"{best}-{args.source}-{datetime.now(UTC).replace(tzinfo=None):%Y%m%d}-s{args.seed}"
    out = Path(args.out) / tag
    if out.exists():
        # Two runs on the same day would otherwise share a tag and the second would overwrite the
        # first candidate, so a report could be re-attributed to different content.
        tag = f"{tag}-{hashlib.sha256(f'{args.source}{args.seed}{t0}'.encode()).hexdigest()[:6]}"
        out = Path(args.out) / tag
    out.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, out / "model.joblib")
    joblib.dump(iso, out / "calibrator.joblib")
    # The SHAP background is a published artifact, so it is sampled only from non-personal rows:
    # a vector drawn from someone's real mail is derived personal data even without any text in it.
    bg_pool = np.arange(len(Xf))
    if personal is not None and personal.any():
        bg_pool = bg_pool[~personal[fit]]
        if len(bg_pool) == 0:
            raise SystemExit("no non-personal rows left for the SHAP background sample")
        print(f"SHAP background sample: {len(bg_pool)} non-personal rows "
              f"({int(personal[fit].sum())} personal rows excluded)")
    bg_pick = np.random.RandomState(args.seed).choice(bg_pool, min(100, len(bg_pool)), replace=False)
    personal_in_background = int(personal[fit][bg_pick].sum()) if personal is not None else 0
    if personal_in_background:
        raise SystemExit("refusing to write a SHAP background sample that contains personal rows")
    np.save(out / "background.npy", Xf[bg_pick])
    provenance["background_rows"] = int(len(bg_pick))
    provenance["background_rows_personal"] = personal_in_background
    provenance["fit_rows_personal"] = int(personal[fit].sum()) if personal is not None else 0
    meta = {"version_tag": tag, "algorithm": best, "trained_at": datetime.now(UTC).replace(tzinfo=None).isoformat(timespec="seconds"),
            "feature_names": FEATURE_NAMES, "data_source": data_source, "n_samples": int(len(y)),
            "split": {"fit": len(fit), "validation": len(val), "test": len(test), "mode": args.split},
            "operating_points": ops,
            "seed_sweep": sweep,
            "training": provenance,
            "reason_min_contribution": REASON_MIN[best], "fpr_ceiling": FPR_CEILING,
            "metrics": {k: float(v) for k, v in selected_test.items() if not k in ("tn", "fp", "fn", "tp")}}
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    active = Path(args.out) / "active"
    if args.activate:
        check_activation_allowed(provenance, args.allow_personal_data)
        activate(out, active)
        print(f"activated {tag} -> {active}")
    else:
        print(f"candidate model written to {out}. Not activated; pass --activate to replace {active}.")

    rep_dir = Path(args.reports)
    rep_dir.mkdir(parents=True, exist_ok=True)
    full = {"meta": meta, "validation": results_val, "test": results_test, "selected_calibrated_test": selected_test,
            "operating_points": ops, "seed_sweep": sweep, "ablation_xgboost": ablation}
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
