"""Can the features tell which CORPUS a message came from?

The reviewer's test, in two parts.

**Part A - the false-positive claim.** Take legitimate mail only, from corpora
with different providers and eras, and train a classifier to predict the
SOURCE. If the features encode the provider or the era rather than the message
being legitimate, then the measured false-positive rate does not transfer to
another person's mailbox. Chance is 1/n.

**Part B - the shortcut test.** Add the phishing corpora and ask the same
question across all of them. A source that is perfectly separable has a
fingerprint, and a model trained on it will learn the fingerprint instead of
the content.

Three feature sets are scored, because the point is to find out WHICH features
are the leak:

1. the 65 features the model actually uses
2. the format features alone - header names, Date and Message-ID shape,
   charset, MIME structure, line endings, Received-chain length
3. the format features with the transport headers removed - no Received, no
   X-Gmail-*, no ARC-*, no Authentication-Results, no Return-Path

If the leak survives (3), it is in something the model actually needs and the
fix is a different corpus. If it disappears, the leak was the transport and
the fix is to not train on those headers.

Needs the gitignored corpora, so this is a script and not a pytest case:

    cd backend
    python -m scripts.source_leak_test --out reports/leak
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.features.common import ExtractionContext  # noqa: E402
from app.features.feature_vector import FEATURE_GROUP, FEATURE_NAMES, extract_all  # noqa: E402
from app.ingestion.email_parser import parse_email  # noqa: E402
from training import corpus  # noqa: E402
from training.format_features import (PROVIDER_HEADERS, format_feature_names,  # noqa: E402
                                      format_features, normalised_format_features)

RAW = ROOT / "data" / "raw"
CAP = 1500
SEED = 7
CACHE = Path(tempfile.gettempdir())


def ham_sources() -> dict[str, list]:
    """Legitimate mail only, one bucket per corpus."""
    out: dict[str, list] = {}
    mailbox = RAW / "mailbox"
    if mailbox.exists():
        out["mailbox (2020-2026, owner)"] = corpus.load_mailbox(mailbox, label=0, limit=CAP)
    sa = RAW / "spamassassin"
    if sa.exists():
        out["spamassassin (2003)"] = (corpus.load_dir(sa / "easy_ham", 0, limit=CAP)
                                      + corpus.load_dir(sa / "hard_ham", 0, limit=CAP))
    ceas = RAW / "kaggle" / "ceas08" / "legitimate"
    if ceas.exists():
        out["ceas (2008)"] = corpus.load_dir(ceas, 0, limit=CAP)
    return {k: v for k, v in out.items() if v}


def phish_sources() -> dict[str, list]:
    """Phishing corpora, one bucket each."""
    out: dict[str, list] = {}
    nazario = RAW / "nazario"
    if nazario.exists():
        out["nazario (2004-2025)"] = corpus.load_dir(nazario, 1, limit=CAP)
    pot = RAW / "phishing_pot"
    if pot.exists():
        out["phishing_pot (2022+)"] = corpus.load_dir(pot, 1, limit=CAP)
    return {k: v for k, v in out.items() if v}


def featurise_65(samples: list) -> np.ndarray:
    ctx = ExtractionContext()
    rows = []
    for s in samples:
        try:
            rows.append(extract_all(parse_email(s.raw), ctx).vector)
        except Exception:
            continue
    return np.asarray(rows, dtype=float)


def featurise_format(samples: list, normalised: bool) -> np.ndarray:
    fn = normalised_format_features if normalised else format_features
    return np.asarray([fn(s.raw) for s in samples], dtype=float)


def source_report(X: np.ndarray, y: np.ndarray, names: list[str], title: str,
                  order: list[str]) -> dict:
    """How well can a classifier recover the corpus, and which features do it?"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split

    if len(set(y.tolist())) < 2 or len(y) < 20:
        return {"title": title, "skipped": "not enough data"}
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=SEED, stratify=y)
    clf = RandomForestClassifier(n_estimators=300, random_state=SEED, class_weight="balanced")
    clf.fit(X_tr, y_tr)
    pred = clf.predict(X_te)
    acc = float(accuracy_score(y_te, pred))
    chance = 1.0 / len(set(y.tolist()))
    classes = sorted(set(y.tolist()))
    print(f"\n--- {title} ---")
    print(f"  n={len(X)}  classes={len(classes)}  chance={chance:.3f}  accuracy={acc:.3f}"
          f"  {'LEAK' if acc > chance + 0.10 else 'no strong leak'}")
    importances = sorted(zip(clf.feature_importances_, range(len(names))), reverse=True)[:8]
    for score, idx in importances:
        means = [float(X[y == c, idx].mean()) for c in classes]
        print(f"    {names[idx]:34s} imp={score:.3f}  " +
              " ".join(f"{order[c][:12]}={m:.3f}" for c, m in zip(classes, means)))
    print("    confusion (rows=truth, cols=predicted):")
    confusion = {}
    for c in classes:
        row = [int(((y_te == c) & (pred == p)).sum()) for p in classes]
        confusion[order[c]] = {order[p]: row[i] for i, p in enumerate(classes)}
        print(f"      {order[c][:20]:22s} {row}")
    return {
        "title": title, "n": int(len(X)), "chance": round(chance, 4),
        "accuracy": round(acc, 4), "leak": bool(acc > chance + 0.10),
        "confusion": confusion,
        "top_features": [{"feature": names[i], "importance": round(float(s), 4),
                          "per_source_mean": {order[c]: round(float(X[y == c, i].mean()), 4)
                                              for c in classes}}
                         for s, i in importances],
    }


def _cache_path(tag: str) -> Path:
    return CACHE / f"phishlens_leak_{tag}.npy"


def build_matrices(sources: dict[str, list]) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The three feature matrices and the labels, cached per corpus."""
    labels, m65, mfmt, mnorm = [], [], [], []
    for label, samples in enumerate(sources.values()):
        name = list(sources)[label]
        capped = samples[:CAP]
        c65, cfmt, cnorm = _cache_path(f"65_{label}"), _cache_path(f"fmt_{label}"), _cache_path(f"norm_{label}")
        if c65.exists() and cfmt.exists() and cnorm.exists():
            X65, Xfmt, Xnorm = np.load(c65), np.load(cfmt), np.load(cnorm)
        else:
            X65 = featurise_65(capped)
            Xfmt = featurise_format(capped, normalised=False)
            Xnorm = featurise_format(capped, normalised=True)
            np.save(c65, X65)
            np.save(cfmt, Xfmt)
            np.save(cnorm, Xnorm)
        print(f"  {name}: {len(capped)} messages")
        m65.append(X65)
        mfmt.append(Xfmt)
        mnorm.append(Xnorm)
        labels.append(np.full(len(capped), label))
    return np.vstack(m65), np.vstack(mfmt), np.vstack(mnorm), np.concatenate(labels)


def ablation(X: np.ndarray, y: np.ndarray, names: list[str], title: str) -> dict:
    """Which feature is the leak?

    Drop one feature at a time and re-measure how well the corpus can still be
    recovered. The features whose removal collapses the accuracy are the
    carriers, and dropping all of them is the fix.
    """
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split

    if len(set(y.tolist())) < 2:
        return {"title": title, "skipped": "not enough data"}

    def accuracy(cols: list[int]) -> float:
        X_tr, X_te, y_tr, y_te = train_test_split(X[:, cols], y, test_size=0.3,
                                                    random_state=SEED, stratify=y)
        clf = RandomForestClassifier(n_estimators=200, random_state=SEED, class_weight="balanced")
        clf.fit(X_tr, y_tr)
        return float(accuracy_score(y_te, clf.predict(X_te)))

    all_cols = list(range(X.shape[1]))
    base = accuracy(all_cols)
    chance = 1.0 / len(set(y.tolist()))
    print(f"\n--- ablation: {title} ---")
    print(f"  baseline accuracy={base:.3f} (chance {chance:.3f}), {X.shape[1]} features")
    drops = []
    for i in all_cols:
        acc = accuracy([c for c in all_cols if c != i])
        drops.append({"feature": names[i], "accuracy_without_it": round(acc, 4),
                      "drop": round(base - acc, 4)})
    drops.sort(key=lambda d: -d["drop"])
    print("  the features whose removal hurts the most (these are the carriers):")
    for d in drops[:8]:
        print(f"    {d['feature']:34s} without it: {d['accuracy_without_it']:.3f}  (-{d['drop']:.3f})")

    # Removing one feature at a time is not enough: the leak is REDUNDANT, because several
    # features each independently identify the corpus. The actionable question is what happens
    # when a whole CLASS of features goes, so the groups are dropped as blocks.
    blocks = _blocks(names)
    block_results = []
    print("  dropping a whole class of features at once:")
    for block, cols in blocks.items():
        keep = [c for c in all_cols if c not in cols]
        if not keep:
            continue
        acc = accuracy(keep)
        block_results.append({"block": block, "features_removed": len(cols),
                              "accuracy_without_block": round(acc, 4),
                              "leak_survives": bool(acc > chance + 0.10)})
        print(f"    without {block:14s} ({len(cols):2d} features): accuracy={acc:.3f}"
              f"  {'LEAK SURVIVES' if acc > chance + 0.10 else 'no strong leak'}")

    carriers = [d["feature"] for d in drops if d["drop"] > 0.02]
    idx = [i for i, n in enumerate(names) if n not in carriers]
    after = accuracy(idx) if idx else base
    print(f"  dropping all {len(carriers)} single-feature carriers at once: accuracy={after:.3f}"
          f"  {'LEAK SURVIVES' if after > chance + 0.10 else 'no strong leak'}")
    return {"title": title, "baseline_accuracy": round(base, 4), "chance": round(chance, 4),
            "single_feature_carriers": carriers,
            "accuracy_without_carriers": round(after, 4),
            "leak_survives": bool(after > chance + 0.10),
            "blocks": block_results,
            "per_feature": drops}


def _blocks(names: list[str]) -> dict[str, list[int]]:
    """The classes of features, for the block ablation."""
    if names and names[0].startswith("header:"):
        out: dict[str, list[int]] = {}
        for i, n in enumerate(names):
            key = n.split(":", 1)[0]
            if key == "header":
                key = "header (all)"
            out.setdefault(key, []).append(i)
        return out
    out = {}
    for i, n in enumerate(names):
        out.setdefault(FEATURE_GROUP.get(n, "other"), []).append(i)
    return out


def cross_corpus_fpr(matrices: dict[str, np.ndarray], phish_X: np.ndarray, seed: int = SEED) -> list[dict]:
    """What is the corpus information worth?

    The corpus-classifier test says the features carry corpus information. This
    test says what that information is worth: train a detector on ONE corpus's
    legitimate mail plus the phishing, then measure the false-positive rate on
    every OTHER corpus's legitimate mail.

    If the detector flags another corpus's ham as phishing, then the measured
    false-positive rate does not transfer to another person's inbox, and no
    amount of feature engineering in this project will change that.
    """
    from sklearn.ensemble import RandomForestClassifier

    if not phish_X.size or len(matrices) < 2:
        return []
    out = []
    for train_name, X_ham_train in matrices.items():
        X = np.vstack([X_ham_train, phish_X])
        y = np.concatenate([np.zeros(len(X_ham_train)), np.ones(len(phish_X))])
        clf = RandomForestClassifier(n_estimators=200, random_state=seed, class_weight="balanced").fit(X, y)
        for test_name, X_ham_test in matrices.items():
            if test_name == train_name:
                continue
            p = clf.predict_proba(X_ham_test)[:, 1]
            out.append({
                "trained_on": train_name,
                "tested_on": test_name,
                "fpr_at_0_5": float(np.mean(p >= 0.5)),
                "mean_probability": float(np.mean(p)),
                "flagged_median_probability": float(np.median(p)),
            })
    return out


def run(sources: dict[str, list], tag: str, phish_samples: list | None = None) -> dict:
    order = list(sources)
    X65, Xfmt, Xnorm, y = build_matrices(sources)
    fmt_names = format_feature_names()

    print(f"\n=== {tag}: can the corpus be recovered? ===")
    header_idx = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP.get(n) == "header"]
    results = [
        source_report(X65, y, FEATURE_NAMES, "the 65 features the model uses", order),
        source_report(X65[:, header_idx], y, [FEATURE_NAMES[i] for i in header_idx],
                      "the 13 header/format features only", order),
        source_report(Xfmt, y, fmt_names, "format features only (raw headers)", order),
        source_report(Xnorm, y, fmt_names, "format features, transport headers removed", order),
    ]
    abl = [ablation(X65, y, FEATURE_NAMES, "the 65 features"),
           ablation(Xfmt, y, fmt_names, "the format features")]

    cross = []
    if phish_samples:
        print(f"\n--- cross-corpus false-positive rate (train on one corpus's ham, test on the others) ---")
        ham_matrices = {}
        offset = 0
        for label, name in enumerate(order):
            ham_matrices[name] = X65[offset:offset + len(sources[name][:CAP])]
            offset += len(sources[name][:CAP])
        Xp = featurise_65(phish_samples[:CAP])
        cross = cross_corpus_fpr(ham_matrices, Xp)
        for row in cross:
            print(f"    trained on {row['trained_on'][:24]:26s} -> {row['tested_on'][:24]:26s} "
                  f"FPR {row['fpr_at_0_5']:.3f}  median p {row['flagged_median_probability']:.3f}")
    return {"corpora": order, "results": results, "ablation": abl, "cross_corpus_fpr": cross,
            "provider_headers": sorted(PROVIDER_HEADERS)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="reports/leak", help="directory for the JSON report")
    ap.add_argument("--skip-phishing", action="store_true",
                    help="run only the legitimate-mail part")
    args = ap.parse_args()

    print("loading legitimate mail from each corpus ...")
    ham = ham_sources()
    if not ham:
        raise SystemExit("No legitimate corpora found under backend/data/raw. "
                         "Run python -m training.download_datasets first.")
    phish = phish_sources()
    report = {"legitimate_only": run(ham, "Part A: legitimate mail only",
                                     phish_samples=phish.get("phishing_pot (2022+)") or [])}

    if phish and not args.skip_phishing:
        print("\nloading phishing mail from each corpus ...")
        everything = {**ham, **phish}
        report["with_phishing"] = run(everything, "Part B: every corpus")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "source_leak.json").write_text(json.dumps(report, indent=2))
    print(f"\nwrote {out / 'source_leak.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
