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
from pathlib import Path, PurePosixPath

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
    return X, y, groups, p_raw, p_cal, scores


def probability_summary(p) -> dict:
    """Distribution summary for a probability vector, so raw and calibrated scores can be compared."""
    p = np.asarray(p, dtype=float)
    if p.size == 0:
        return {"mean": 0.0, "median": 0.0, "p90": 0.0, "share_above_0_29": 0.0, "share_above_0_5": 0.0}
    return {
        "mean": float(p.mean()),
        "median": float(np.median(p)),
        "p90": float(np.percentile(p, 90)),
        "share_above_0_29": float(np.mean(p >= 0.29)),
        "share_above_0_5": float(np.mean(p >= 0.5)),
    }


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


def recall_at_fixed_fpr(y, p_cal, fpr_targets=(0.01, 0.05)) -> dict:
    """How much phishing do we catch if we only flag a given share of legitimate mail?

    For a triage tool this is the operating question: the analyst only looks at
    what the system flags, so the useful number is the recall at a false-positive
    rate the analyst can tolerate, not the recall at an arbitrary probability.
    """
    negatives = np.asarray(p_cal)[y == 0]
    positives = np.asarray(p_cal)[y == 1]
    if negatives.size == 0 or positives.size == 0:
        return {}
    out = {}
    for target in fpr_targets:
        keep = int(np.floor(target * negatives.size))
        if keep <= 0:
            threshold = float(np.max(negatives)) + 1e-9
        else:
            candidate = float(np.sort(negatives)[::-1][keep - 1])
            if int(np.sum(negatives >= candidate)) > keep:
                # The boundary value is shared by more legitimate messages than the budget
                # allows, so the threshold has to sit above it.
                higher = negatives[negatives > candidate]
                threshold = float(np.min(higher)) if higher.size else candidate + 1e-9
            else:
                threshold = candidate
        flagged_ham = int(np.sum(negatives >= threshold))
        flagged_phish = int(np.sum(positives >= threshold))
        out[f"at_fpr_{target:g}"] = {
            "threshold": threshold,
            "fpr": float(flagged_ham / negatives.size),
            "recall": float(flagged_phish / positives.size),
            "precision": float(flagged_phish / max(1, flagged_phish + flagged_ham)),
            "flagged_ham": flagged_ham,
            "flagged_phishing": flagged_phish,
        }
    return out


def reliability(y, p_cal, scores, low_max: int, high_min: int) -> dict:
    """Does the score mean what it says?

    Per risk band: how many messages landed there, the mean predicted probability,
    and the phishing rate actually observed. A band whose observed rate is nowhere
    near its mean probability is not calibrated, and the band boundaries are
    meaningless.
    """
    out = {}
    for band, mask in (("LOW", scores <= low_max),
                       ("MEDIUM", (scores > low_max) & (scores < high_min)),
                       ("HIGH", scores >= high_min)):
        n = int(mask.sum())
        if n == 0:
            out[band] = {"n": 0}
            continue
        out[band] = {
            "n": n,
            "mean_predicted_probability": float(np.mean(p_cal[mask])),
            "observed_phishing_rate": float(np.mean(y[mask])) if len(np.unique(y)) > 1 else None,
            "phishing_messages": int(np.sum(y[mask])),
        }
    return out


def probability_bins(y, p_cal, bins: int = 10) -> list:
    """A reliability curve: predicted probability against observed rate, in ten bins."""
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (p_cal >= lo) & ((p_cal < hi) if i < bins - 1 else (p_cal <= hi))
        n = int(mask.sum())
        if n == 0:
            continue
        rows.append({
            "range": [round(float(lo), 2), round(float(hi), 2)],
            "n": n,
            "mean_predicted": float(np.mean(p_cal[mask])),
            "observed_rate": float(np.mean(y[mask])) if len(np.unique(y)) > 1 else None,
        })
    return rows


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


def _cli_date(value: str | None, flag: str) -> datetime | None:
    """Parse a CLI date, turning a malformed value into a readable error."""
    if not value:
        return None
    try:
        return parse_cli_date(value)
    except ValueError as exc:
        raise SystemExit(f"{flag} must be an ISO date such as 2024-01-01, got {value!r} ({exc})") from exc


def leakage_check(meta: dict, since: datetime | None, until: datetime | None,
                  min_key: str = "phish_min_date", max_key: str = "phish_max_date") -> str:
    """Is the model's training range disjoint from the evaluation window?

    'clear'    - the model never trained on data from this window.
    'overlap'  - it did, so the window is in-sample and its numbers are not generalization results.
    'unknown'  - the model carries no training provenance for this side (pre-provenance artefacts).
    """
    training = (meta or {}).get("training") or {}
    lo = _parse_iso(training.get(min_key))
    hi = _parse_iso(training.get(max_key))
    if lo is None or hi is None:
        return "unknown"
    since_b = since or datetime.min.replace(tzinfo=timezone.utc)
    until_b = until or datetime.max.replace(tzinfo=timezone.utc)
    return "overlap" if (lo < until_b and hi >= since_b) else "clear"


def phish_leakage(meta: dict, eval_phish_dir: str, since: datetime | None, until: datetime | None) -> tuple[str, list[str]]:
    """Is the evaluation phishing corpus disjoint from the archives the model trained on?

    The split is by archive file, because the corpus dates are unreliable: some Nazario archives carry
    dates from 1970 to 2038 and 65 messages in the 2015-2025 archives have no date at all, so a
    date-based check admits holdout messages into training and then calls them held out. A model
    trained before the file list existed cannot be checked that way, so it fails closed.

    Returns the status and the list of archive files that appear on both sides.
    """
    training = (meta or {}).get("training") or {}
    trained_files = training.get("phish_files")
    if trained_files is None:
        return "unknown", []
    # The training side records "<corpus label>/<archive>" when more than one corpus was used, and
    # a bare archive name for a single corpus. Both are compared by their last path component,
    # because the same archive name in two directories is most likely the same archive: the Kaggle
    # phishing set republishes Nazario, so an archive called phishing-2024.mbox on both sides is a
    # leak until proven otherwise.
    trained = {PurePosixPath(f).name for f in trained_files}
    eval_files = {PurePosixPath(f).name for f in corpus.source_files(eval_phish_dir)}
    overlap = sorted(trained & eval_files)
    if overlap:
        return "overlap", overlap
    # A corpus of one message per file is recorded by a digest of its names rather than the names
    # themselves, so the evaluated corpus is matched against the recorded digests.
    eval_digest = corpus.name_digest(corpus.source_files(eval_phish_dir))
    for source in training.get("phish_sources") or []:
        if source.get("name_digest") == eval_digest:
            return "overlap", [source.get("label", "?")]
    return "clear", []


def _path_ids(path: Path) -> set[str]:
    """Non-reversible identifiers for a path and, for a file, the directory that contains it.

    Storing a digest instead of the path keeps a local account name out of a published artifact
    while still letting the harness decide whether two mailbox locations are the same source.
    """
    return corpus.path_digests(path)


def ham_leakage(meta: dict, eval_mailbox: str, since: datetime | None, until: datetime | None) -> str:
    """Is the evaluation mailbox disjoint from the mailbox the model trained on?

    'distinct' - the model trained on a different mailbox, so the two cannot share messages.
    'clear'    - same source, but the training dates fall outside the evaluation window.
    'overlap'  - same source and the training dates fall inside the window.
    'unknown'  - the model records no mailbox provenance, or the two locations cannot be compared.

    The comparison is by path digest, and it is deliberately conservative: a model trained on a
    directory and evaluated on a file inside that directory is the same source, and a model trained
    on a file and evaluated on a directory that may contain it is 'unknown' rather than 'distinct',
    because a directory load reads every mbox beneath it.
    """
    training = (meta or {}).get("training") or {}
    trained_id = training.get("legit_mailbox_id")
    trained_scope = training.get("legit_mailbox_scope")
    if not trained_id:
        return "unknown"
    eval_path = Path(eval_mailbox)
    if trained_id in corpus.path_digests(eval_path):
        return leakage_check(meta, since, until, "legit_mailbox_min_date", "legit_mailbox_max_date")
    if trained_scope == "file" and eval_path.is_dir():
        # The evaluated directory may contain the file the model trained on.
        return "unknown"
    return "distinct"


def guard_leakage(status: str, model_tag: str, allow_overlap: bool, allow_unknown: bool = False) -> None:
    """Refuse to report a window the model may have trained on.

    'overlap'  - the model trained on data from this window: the numbers would be in-sample.
    'unknown'  - the model carries no training provenance, so it cannot be proven disjoint. A model
                  trained before the provenance block existed would otherwise pass silently, which is
                  exactly the case this guard exists for.
    """
    if status == "overlap" and not allow_overlap:
        raise SystemExit(
            f"Refusing to report this window: model {model_tag} was trained on data dated inside it, "
            "so the numbers would be in-sample. Retrain with --phish-until / --legit-until (see "
            "docs/19-teammate-training-guide.md) or pass --allow-training-overlap to score anyway.")
    if status == "unknown" and not allow_unknown:
        raise SystemExit(
            f"Refusing to report this window: model {model_tag} carries no training provenance, so it cannot be "
            "shown to be disjoint from the window. Score a model trained with the current training code, or "
            "pass --allow-unknown-provenance to score anyway (the result is then unverified, not clean).")


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
        "fpr_at_probability_0_29": float(np.mean(p_cal >= 0.29)),
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
        "recall_at_probability_0_29": float(np.mean(p_cal >= 0.29)),
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
        f"- Training leakage check: **{leak.get('status', 'unknown')}** "
        f"(phish: {leak.get('phish', {}).get('status', 'unknown')}, "
        f"ham: {leak.get('ham', {}).get('status', 'unknown')})",
        "", "## Mailbox ham", "",
        f"- Loaded: {m['count']}",
        f"- Date range: {m['date_range']['min']} to {m['date_range']['max']}",
        f"- FPR at probability 0.5: **{m['fpr_at_probability_0_5']:.3f}**",
        f"- FPR at probability 0.29: **{m['fpr_at_probability_0_29']:.3f}**",
        f"- FPR at LOW/MEDIUM boundary: **{m['fpr_at_band_boundary']:.3f}**",
        f"- FPR at LOW/MEDIUM boundary, domain-macro: **{m.get('fpr_at_band_boundary_macro', 0.0):.3f}**",
        f"- 95% CI (pooled): {ci[0]:.3f} - {ci[1]:.3f}",
        f"- Sender domains: {m.get('sender_domains', 0)}; largest domain share: {m.get('max_domain_share', 0.0):.3f}",
        f"- Band counts: {m['band_counts']}",
        f"- Auth missing rate: {m['auth']['auth_missing']:.3f}",
        f"- Raw probability mean: {m['raw_probability']['mean']:.4f} "
        f"(share above 0.29: {m['raw_probability']['share_above_0_29']:.3f})",
        f"- Calibrated probability mean: {m['calibrated_probability']['mean']:.4f} "
        f"(share above 0.29: {m['calibrated_probability']['share_above_0_29']:.3f})",
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
                  f"- Recall at probability 0.29: **{p['recall_at_probability_0_29']:.3f}**",
                  f"- Recall at LOW/MEDIUM boundary: **{p['recall_at_band_boundary']:.3f}**",
                  f"- Band counts: {p['band_counts']}"]
    if report.get("combined"):
        c = report["combined"]
        lines += ["", "## Combined", "",
                  f"- Samples: {c['count']} ({c['positives']} phishing, {c['negatives']} ham)",
                  f"- F1 at probability 0.5: **{c['at_probability_0_5']['f1']:.3f}**",
                  f"- F1 at LOW/MEDIUM boundary: **{c['at_band_boundary']['f1']:.3f}**"]
        for name, row in (c.get("recall_at_fixed_fpr") or {}).items():
            lines.append(f"- Recall at FPR {name.removeprefix('at_fpr_')}: "
                         f"**{row['recall']:.3f}** (precision {row['precision']:.3f}, "
                         f"threshold {row['threshold']:.4f})")
        bands = (c.get("calibration") or {}).get("bands") or {}
        if bands:
            lines += ["", "### Calibration by risk band", "",
                      "| band | n | mean predicted | observed phishing rate |", "|---|---:|---:|---:|"]
            for band in ("LOW", "MEDIUM", "HIGH"):
                row = bands.get(band, {})
                if not row.get("n"):
                    continue
                observed = row.get("observed_phishing_rate")
                lines.append(f"| {band} | {row['n']} | {row['mean_predicted_probability']:.3f} | "
                             + (f"{observed:.3f}" if observed is not None else "-") + " |")
    return "\n".join(lines) + "\n"


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", default="models", help="directory that holds the active model")
    ap.add_argument("--model", default=None,
                    help="path to a candidate model directory (as written by training/train.py) instead of active")
    ap.add_argument("--mailbox", default="data/raw/mailbox/All mail Including Spam and Trash.mbox")
    ap.add_argument("--mailbox-since", default=None, help="only score mailbox messages dated on/after this date")
    ap.add_argument("--mailbox-until", default=None, help="only score mailbox messages dated before this date")
    ap.add_argument("--phish-dir", default="data/raw/nazario")
    ap.add_argument("--phish-since", default=DEFAULT_PHISH_SINCE)
    ap.add_argument("--phish-until", default=DEFAULT_PHISH_UNTIL)
    ap.add_argument("--allow-training-overlap", action="store_true",
                    help="score even when the model was trained on phishing or legitimate mail from this window "
                         "(in-sample on that side)")
    ap.add_argument("--allow-unknown-provenance", action="store_true",
                    help="score even when the model carries no training provenance, so the window cannot be "
                         "proven disjoint. The result is unverified, not clean")
    ap.add_argument("--out", default="reports/modern")
    args = ap.parse_args(argv)

    settings = Settings()
    bundle = load_model_dir(Path(args.model)) if args.model else load_active(Path(args.model_dir))
    since = _cli_date(args.phish_since, "--phish-since")
    until = _cli_date(args.phish_until, "--phish-until")
    m_since = _cli_date(args.mailbox_since, "--mailbox-since")
    m_until = _cli_date(args.mailbox_until, "--mailbox-until")
    phish_leak, phish_overlap_files = phish_leakage(bundle.meta, args.phish_dir, since, until)
    ham_leak = ham_leakage(bundle.meta, args.mailbox, m_since, m_until)
    leak_status = "overlap" if "overlap" in (phish_leak, ham_leak) else (
        "clear" if phish_leak == "clear" and ham_leak in ("clear", "distinct") else "unknown")
    guard_leakage(leak_status, bundle.version_tag, args.allow_training_overlap, args.allow_unknown_provenance)

    mailbox_path = Path(args.mailbox)
    if not mailbox_path.exists():
        raise SystemExit(f"Mailbox not found: {mailbox_path}")
    mailbox_stats: dict = {}
    mailbox_samples = corpus.load_mailbox(mailbox_path, label=0, stats=mailbox_stats)
    if args.mailbox_since or args.mailbox_until:
        # One rule for both sides: a message with no date cannot be placed in time, so it is dropped
        # whenever a window is requested and counted in the report.
        mailbox_samples = [s for s in mailbox_samples if in_window(s, m_since, m_until)]
    if not mailbox_samples:
        raise SystemExit(f"No mailbox messages in the requested window at {mailbox_path} "
                         f"(window {args.mailbox_since} to {args.mailbox_until})")
    Xh, yh, gh, ph_raw, ph, sh = score_samples(bundle, mailbox_samples)

    phish_samples = []
    phish_path = Path(args.phish_dir)
    if not phish_path.exists():
        raise SystemExit(f"Phishing directory not found: {phish_path}")
    phish_samples = [s for s in corpus.load_dir(phish_path, 1) if in_window(s, since, until)]
    if not phish_samples:
        raise SystemExit(f"No phishing messages in the requested window at {phish_path} "
                         f"(window {args.phish_since} to {args.phish_until})")

    training = bundle.meta.get("training") or {}
    report = {
        "model": {"version_tag": bundle.version_tag, "algorithm": bundle.algorithm,
                  "path": Path(args.model or Path(args.model_dir) / "active").name},
        "thresholds": {"low_max": settings.band_low_max, "high_min": settings.band_high_min},
        "leakage": {
            "status": leak_status,
            "phish": {"status": phish_leak, "window": {"since": args.phish_since, "until": args.phish_until},
                      "overlap_files": phish_overlap_files,
                      "model_min_date": training.get("phish_min_date"),
                      "model_max_date": training.get("phish_max_date")},
            "ham": {"status": ham_leak,
                    "window": {"since": args.mailbox_since, "until": args.mailbox_until},
                    "model_mailbox_scope": training.get("legit_mailbox_scope"),
                    "model_min_date": training.get("legit_mailbox_min_date"),
                    "model_max_date": training.get("legit_mailbox_max_date")},
        },
        "mailbox": {
            "scope": "directory" if mailbox_path.is_dir() else "file",
            "count": len(mailbox_samples),
            "date_range": _date_range(mailbox_samples),
            "loader_drops": mailbox_stats,
            "raw_probability": probability_summary(ph_raw),
            "calibrated_probability": probability_summary(ph),
            **{k: v for k, v in ham_summary(Xh, ph, sh, gh, settings.band_low_max,
                                           settings.band_high_min).items() if k != "count"},
        },
    }
    if phish_samples:
        Xp, yp, gp, pp_raw, pp, sp = score_samples(bundle, phish_samples)
        report["phish"] = {
            "path": str(args.phish_dir), "window": {"since": args.phish_since, "until": args.phish_until},
            "date_range": _date_range(phish_samples), "count": len(phish_samples),
            "raw_probability": probability_summary(pp_raw),
            "calibrated_probability": probability_summary(pp),
            **phish_summary(pp, sp, settings.band_low_max, settings.band_high_min),
        }
        y_all = np.concatenate([yh, yp])
        p_all = np.concatenate([ph, pp])
        s_all = np.concatenate([sh, sp])
        report["combined"] = {
            "count": int(len(y_all)), "positives": int(y_all.sum()), "negatives": int((1 - y_all).sum()),
            **threshold_metrics(y_all, p_all, s_all, settings.band_low_max),
            "recall_at_fixed_fpr": recall_at_fixed_fpr(y_all, p_all),
            "calibration": {
                "bands": reliability(y_all, p_all, s_all, settings.band_low_max, settings.band_high_min),
                "probability_bins": probability_bins(y_all, p_all),
            },
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
