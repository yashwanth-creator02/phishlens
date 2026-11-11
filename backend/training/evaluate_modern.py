"""Score a serving model on modern mail without training or modifying it.

    python -m training.evaluate_modern
    python -m training.evaluate_modern --model models/<candidate-tag>
    python -m training.evaluate_modern --phish-since 2015-01-01 --phish-until 2024-01-01

The mailbox is legitimate ham (Gmail Spam/Trash/Sent/Drafts/Chat excluded). The phish side is the
Nazario corpus filtered by Date. Both are scored with the same 65-feature extractor used by the API.
This is an evaluation-only path: it never writes a model or copies anything into models/active.

The phishing window defaults to 2015-2024 so that the 2024-2025 Nazario archives stay a holdout.
If the model carries training provenance that overlaps the window, the run aborts instead of
reporting in-sample recall as a generalization result.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, roc_auc_score

from app.core.config import Settings
from app.features.feature_vector import FEATURE_NAMES
from app.ml.registry import ModelBundle, load_active, load_model_dir
from app.scoring.risk_bands import band_for, to_score

from . import corpus
from .corpus import date_range, in_window, parse_cli_date, parse_date
from .synthetic import Sample, samples_to_matrix

DEFAULT_PHISH_SINCE = "2015-01-01"
DEFAULT_PHISH_UNTIL = "2024-01-01"


def score_samples(bundle: ModelBundle, samples: list[Sample]):
    X, y, groups = samples_to_matrix(samples)
    p_raw = bundle.model.predict_proba(X)[:, 1]
    p_cal = bundle.calibrator.predict(p_raw) if bundle.calibrator is not None else p_raw
    p_cal = np.clip(np.asarray(p_cal, dtype=float), 0.0, 1.0)
    scores = np.asarray([to_score(float(p)) for p in p_cal], dtype=int)
    return X, y, groups, p_cal, scores


def _binary_metrics(y, pred) -> dict:
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    f1 = 2 * precision * recall / max(1e-12, precision + recall)
    return {
        "precision": float(precision), "recall": float(recall), "f1": float(f1),
        "fpr": float(fp / max(1, fp + tn)), "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
    }


def threshold_metrics(y, p_cal, scores, low_max: int) -> dict:
    out = {
        "at_probability_0_5": _binary_metrics(y, (p_cal >= 0.5).astype(int)),
        "at_band_boundary": _binary_metrics(y, (scores > low_max).astype(int)),
    }
    if len(np.unique(y)) > 1:
        out["roc_auc"] = float(roc_auc_score(y, p_cal))
        out["pr_auc"] = float(average_precision_score(y, p_cal))
    return out


def _band_counts(scores, low_max: int, high_min: int) -> dict:
    counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for score in scores:
        counts[band_for(int(score), low_max, high_min)] += 1
    return counts


def _feature_rates(X, indices: list[str]) -> dict:
    return {name: float(np.mean(X[:, FEATURE_NAMES.index(name)] == 1)) for name in indices}


def fpr_with_ci(flagged, groups, n_boot: int = 1000, seed: int = 7) -> dict:
    """Pooled and domain-macro false-positive rate with a bootstrap 95% CI.

    The macro rate is the unweighted mean of the per-domain rates, so one dominant sender
    domain cannot hide behind a good pooled number. The bootstrap resamples domains, which is
    the unit the statistic is averaged over.
    """
    flagged = np.asarray(flagged, dtype=float)
    groups = np.asarray([str(g) for g in groups])
    if flagged.size == 0:
        return {"pooled": 0.0, "macro": 0.0, "pooled_ci95": [0.0, 0.0], "macro_ci95": [0.0, 0.0], "domains": 0}
    domains = sorted(set(groups.tolist()))
    totals = {d: int((groups == d).sum()) for d in domains}
    hits = {d: float(flagged[groups == d].sum()) for d in domains}
    rates = {d: hits[d] / totals[d] for d in domains}
    pooled = float(flagged.mean())
    macro = float(np.mean(list(rates.values())))
    rng = np.random.default_rng(seed)
    idx_by_domain = {d: np.where(groups == d)[0] for d in domains}
    boot_pooled, boot_macro = [], []
    for _ in range(n_boot):
        picks = rng.choice(domains, size=len(domains), replace=True)
        idx = np.concatenate([idx_by_domain[d] for d in picks])
        boot_pooled.append(float(flagged[idx].mean()))
        boot_macro.append(float(np.mean([rates[d] for d in picks])))
    return {
        "pooled": pooled,
        "macro": macro,
        "pooled_ci95": [float(np.percentile(boot_pooled, 2.5)), float(np.percentile(boot_pooled, 97.5))],
        "macro_ci95": [float(np.percentile(boot_macro, 2.5)), float(np.percentile(boot_macro, 97.5))],
        "domains": len(domains),
    }


def _parse_iso(value: str | None) -> datetime | None:
    """Parse an ISO timestamp from model metadata, tolerating missing or malformed values."""
    if not value:
        return None
    try:
        return parse_cli_date(value)
    except ValueError:
        return None


def leakage_check(meta: dict, since: datetime | None, until: datetime | None) -> str:
    """Is the model's training phishing range disjoint from the evaluation window?

    'clear'    - the model never saw phishing from this window.
    'overlap'  - it did, so the window is in-sample and its recall is not a generalization result.
    'unknown'  - the model carries no training provenance (pre-provenance artefacts).
    """
    training = (meta or {}).get("training") or {}
    lo = _parse_iso(training.get("phish_min_date"))
    hi = _parse_iso(training.get("phish_max_date"))
    if lo is None or hi is None:
        return "unknown"
    since_b = since or datetime.min.replace(tzinfo=timezone.utc)
    until_b = until or datetime.max.replace(tzinfo=timezone.utc)
    return "overlap" if (lo < until_b and hi >= since_b) else "clear"


def guard_leakage(status: str, model_tag: str, allow: bool) -> None:
    if status == "overlap" and not allow:
        raise SystemExit(
            f"Refusing to report this window: model {model_tag} was trained on phishing dated inside it, "
            "so the numbers would be in-sample. Retrain with --phish-until (see docs/19-teammate-training-guide.md) "
            "or pass --allow-training-overlap to score anyway.")


def ham_summary(X, p_cal, scores, groups, low_max: int, high_min: int) -> dict:
    flagged = scores > low_max
    by_domain: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "flagged": 0})
    for group, hit in zip(groups, flagged):
        domain = str(group).removeprefix("legit-mailbox-")
        by_domain[domain]["total"] += 1
        by_domain[domain]["flagged"] += int(hit)
    top = sorted(
        ({"domain": d, **v, "fpr": v["flagged"] / max(1, v["total"])} for d, v in by_domain.items()),
        key=lambda row: (row["flagged"], row["total"]), reverse=True,
    )[:10]
    total = max(1, len(list(flagged)))
    band_rates = fpr_with_ci(flagged, groups)
    return {
        "count": int(len(p_cal)),
        "fpr_at_probability_0_5": float(np.mean(p_cal >= 0.5)),
        "fpr_at_band_boundary": float(np.mean(flagged)),
        "fpr_at_band_boundary_macro": band_rates["macro"],
        "fpr_at_band_boundary_ci95": band_rates["pooled_ci95"],
        "fpr_at_band_boundary_macro_ci95": band_rates["macro_ci95"],
        "sender_domains": band_rates["domains"],
        "max_domain_share": float(max((v["total"] for v in by_domain.values()), default=0) / total),
        "mean_probability": float(np.mean(p_cal)),
        "median_probability": float(np.median(p_cal)),
        "band_counts": _band_counts(scores, low_max, high_min),
        "auth": _feature_rates(X, ["auth_missing", "spf_pass", "dkim_pass", "dmarc_pass"]),
        "header_flags": _feature_rates(X, ["from_returnpath_mismatch", "http_only"]),
        "top_false_positive_domains": top,
    }


def phish_summary(p_cal, scores, low_max: int, high_min: int) -> dict:
    return {
        "count": int(len(p_cal)),
        "recall_at_probability_0_5": float(np.mean(p_cal >= 0.5)),
        "recall_at_band_boundary": float(np.mean(scores > low_max)),
        "mean_probability": float(np.mean(p_cal)),
        "band_counts": _band_counts(scores, low_max, high_min),
    }


def _date_range(samples: list[Sample]) -> dict:
    return date_range(samples)


def _render(report: dict) -> str:
    m = report["mailbox"]
    leak = report.get("leakage", {})
    ci = m.get("fpr_at_band_boundary_ci95", [0.0, 0.0])
    lines = [
        "# Modern mailbox evaluation", "",
        f"- Model: `{report['model']['version_tag']}` ({report['model']['algorithm']})",
        f"- Thresholds: LOW max {report['thresholds']['low_max']}, HIGH min {report['thresholds']['high_min']}",
        f"- Training leakage check: **{leak.get('status', 'unknown')}**",
        "", "## Mailbox ham", "",
        f"- Loaded: {m['count']}",
        f"- Date range: {m['date_range']['min']} to {m['date_range']['max']}",
        f"- FPR at probability 0.5: **{m['fpr_at_probability_0_5']:.3f}**",
        f"- FPR at LOW/MEDIUM boundary: **{m['fpr_at_band_boundary']:.3f}**",
        f"- FPR at LOW/MEDIUM boundary, domain-macro: **{m.get('fpr_at_band_boundary_macro', 0.0):.3f}**",
        f"- 95% CI (pooled): {ci[0]:.3f} - {ci[1]:.3f}",
        f"- Sender domains: {m.get('sender_domains', 0)}; largest domain share: {m.get('max_domain_share', 0.0):.3f}",
        f"- Band counts: {m['band_counts']}",
        f"- Auth missing rate: {m['auth']['auth_missing']:.3f}",
        "", "### Top flagged sender domains", "",
        "| domain | flagged | total | FPR |", "|---|---:|---:|---:|",
    ]
    for row in m["top_false_positive_domains"]:
        lines.append(f"| {row['domain']} | {row['flagged']} | {row['total']} | {row['fpr']:.3f} |")
    if report.get("phish"):
        p = report["phish"]
        lines += ["", "## Modern phishing", "",
                  f"- Loaded: {p['count']}",
                  f"- Window: {p['window']['since']} to {p['window']['until']}",
                  f"- Recall at probability 0.5: **{p['recall_at_probability_0_5']:.3f}**",
                  f"- Recall at LOW/MEDIUM boundary: **{p['recall_at_band_boundary']:.3f}**",
                  f"- Band counts: {p['band_counts']}"]
    if report.get("combined"):
        c = report["combined"]
        lines += ["", "## Combined", "",
                  f"- Samples: {c['count']} ({c['positives']} phishing, {c['negatives']} ham)",
                  f"- F1 at probability 0.5: **{c['at_probability_0_5']['f1']:.3f}**",
                  f"- F1 at LOW/MEDIUM boundary: **{c['at_band_boundary']['f1']:.3f}**"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="models", help="directory that holds the active model")
    ap.add_argument("--model", default=None,
                    help="path to a candidate model directory (as written by training/train.py) instead of active")
    ap.add_argument("--mailbox", default="data/raw/mailbox/All mail Including Spam and Trash.mbox")
    ap.add_argument("--phish-dir", default="data/raw/nazario")
    ap.add_argument("--phish-since", default=DEFAULT_PHISH_SINCE)
    ap.add_argument("--phish-until", default=DEFAULT_PHISH_UNTIL)
    ap.add_argument("--allow-training-overlap", action="store_true",
                    help="score even when the model was trained on phishing from this window (in-sample)")
    ap.add_argument("--out", default="reports/modern")
    args = ap.parse_args(argv)

    settings = Settings()
    bundle = load_model_dir(Path(args.model)) if args.model else load_active(Path(args.model_dir))
    since, until = parse_cli_date(args.phish_since), parse_cli_date(args.phish_until)
    leak_status = leakage_check(bundle.meta, since, until)
    guard_leakage(leak_status, bundle.version_tag, args.allow_training_overlap)

    mailbox_samples = corpus.load_mailbox(args.mailbox, label=0)
    if not mailbox_samples:
        raise SystemExit(f"No mailbox messages found at {args.mailbox}")
    Xh, yh, gh, ph, sh = score_samples(bundle, mailbox_samples)

    phish_samples = []
    phish_path = Path(args.phish_dir)
    if phish_path.exists():
        phish_samples = [s for s in corpus.load_dir(phish_path, 1) if in_window(s, since, until)]

    training = bundle.meta.get("training") or {}
    report = {
        "model": {"version_tag": bundle.version_tag, "algorithm": bundle.algorithm,
                  "path": str(args.model or Path(args.model_dir) / "active")},
        "thresholds": {"low_max": settings.band_low_max, "high_min": settings.band_high_min},
        "leakage": {
            "status": leak_status,
            "window": {"since": args.phish_since, "until": args.phish_until},
            "model_phish_min_date": training.get("phish_min_date"),
            "model_phish_max_date": training.get("phish_max_date"),
        },
        "mailbox": {
            "path": str(args.mailbox),
            "count": len(mailbox_samples),
            "date_range": _date_range(mailbox_samples),
            **{k: v for k, v in ham_summary(Xh, ph, sh, gh, settings.band_low_max,
                                           settings.band_high_min).items() if k != "count"},
        },
    }
    if phish_samples:
        Xp, yp, gp, pp, sp = score_samples(bundle, phish_samples)
        report["phish"] = {
            "path": str(args.phish_dir), "window": {"since": args.phish_since, "until": args.phish_until},
            "date_range": _date_range(phish_samples), "count": len(phish_samples),
            **phish_summary(pp, sp, settings.band_low_max, settings.band_high_min),
        }
        y_all = np.concatenate([yh, yp])
        p_all = np.concatenate([ph, pp])
        s_all = np.concatenate([sh, sp])
        report["combined"] = {
            "count": int(len(y_all)), "positives": int(y_all.sum()), "negatives": int((1 - y_all).sum()),
            **threshold_metrics(y_all, p_all, s_all, settings.band_low_max),
        }

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "evaluation.json").write_text(json.dumps(report, indent=2))
    (out / "evaluation.md").write_text(_render(report))
    print(f"mailbox ham: n={report['mailbox']['count']} "
          f"FPR@0.5={report['mailbox']['fpr_at_probability_0_5']:.3f} "
          f"FPR@band={report['mailbox']['fpr_at_band_boundary']:.3f} "
          f"FPR@band macro={report['mailbox'].get('fpr_at_band_boundary_macro', 0.0):.3f} "
          f"leakage={leak_status}")
    if report.get("phish"):
        print(f"modern phish: n={report['phish']['count']} "
              f"recall@0.5={report['phish']['recall_at_probability_0_5']:.3f} "
              f"recall@band={report['phish']['recall_at_band_boundary']:.3f}")
    print(f"wrote {out / 'evaluation.json'} and {out / 'evaluation.md'}")
    return report


if __name__ == "__main__":
    main()
