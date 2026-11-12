"""Does the 65-feature contract identify WHICH CORPUS a legitimate email came from?

The reviewer's test. If the features encode the mail provider or the era rather
than the message being legitimate, then the phishing model can score an unseen
mailbox on the shape of its provider instead of on its content, and the measured
false-positive rate will not transfer to another person's inbox.

Method: take legitimate mail only, from three corpora with different providers
and eras, and train a classifier to predict the SOURCE. A classifier that does
well has found a shortcut. Chance is 1/3.

The same test is run with the header-and-format features alone, which is where
a provider fingerprint would show up first.

Needs the gitignored corpora, so this is a script and not a pytest case:

    cd backend
    python -m scripts.source_leak_test
"""
from __future__ import annotations

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

RAW = ROOT / "data" / "raw"
CAP = 1500
SEED = 7
CACHE = Path(tempfile.gettempdir())


def load_sources() -> dict[str, list]:
    """Legitimate mail only, one bucket per corpus."""
    return {
        "mailbox (2020-2026, owner)": corpus.load_mailbox(RAW / "mailbox", label=0, limit=CAP),
        "spamassassin (2003)": (corpus.load_dir(RAW / "spamassassin" / "easy_ham", 0, limit=CAP)
                                 + corpus.load_dir(RAW / "spamassassin" / "hard_ham", 0, limit=CAP)),
        "ceas (2008)": corpus.load_dir(RAW / "kaggle" / "ceas08" / "legitimate", 0, limit=CAP),
    }


def featurise(samples: list) -> np.ndarray:
    ctx = ExtractionContext()
    rows = []
    for s in samples:
        try:
            rows.append(extract_all(parse_email(s.raw), ctx).vector)
        except Exception:
            continue
    return np.asarray(rows, dtype=float)


def source_report(X: np.ndarray, y: np.ndarray, title: str) -> None:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=SEED, stratify=y)
    clf = RandomForestClassifier(n_estimators=300, random_state=SEED, class_weight="balanced")
    clf.fit(X_tr, y_tr)
    acc = accuracy_score(y_te, clf.predict(X_te))
    chance = 1.0 / len(set(y.tolist()))
    print(f"\n--- {title} ---")
    print(f"  n={len(X)}  classes={len(set(y.tolist()))}  chance={chance:.3f}  accuracy={acc:.3f}"
          f"  {'LEAK' if acc > chance + 0.10 else 'no strong leak'}")
    importances = sorted(zip(clf.feature_importances_, range(len(FEATURE_NAMES))), reverse=True)[:8]
    for score, idx in importances:
        name = FEATURE_NAMES[idx]
        group = FEATURE_GROUP.get(name, "?")
        means = [float(X[y == c, idx].mean()) for c in sorted(set(y.tolist()))]
        print(f"    {name:28s} [{group:11s}] imp={score:.3f}  per-source mean="
              + " ".join(f"{m:7.3f}" for m in means))
    print("    per-source mean order: 0 = mailbox, 1 = spamassassin 2003, 2 = ceas 2008")
    pred = clf.predict(X_te)
    print("    confusion (rows=truth, cols=predicted):")
    for c in sorted(set(y.tolist())):
        row = [int(((y_te == c) & (pred == p)).sum()) for p in sorted(set(y.tolist()))]
        print(f"      {c}: {row}")


def main() -> int:
    cache_x = CACHE / "phishlens_source_leak_X.npy"
    cache_y = CACHE / "phishlens_source_leak_y.npy"
    if cache_x.exists() and cache_y.exists():
        print("using cached feature matrices")
        X = np.load(cache_x)
        y = np.load(cache_y)
    else:
        print("loading legitimate mail from each corpus ...")
        sources = load_sources()
        labels, matrices = [], []
        for label, samples in enumerate(sources.values()):
            Xs = featurise(samples[:CAP])
            print(f"  {list(sources)[label]}: {len(Xs)} feature vectors")
            labels.append(np.full(len(Xs), label))
            matrices.append(Xs)
        X = np.vstack(matrices)
        y = np.concatenate(labels)
        np.save(cache_x, X)
        np.save(cache_y, y)

    header_idx = [i for i, n in enumerate(FEATURE_NAMES) if FEATURE_GROUP.get(n) == "header"]
    print(f"\nheader/format features ({len(header_idx)}): "
          + ", ".join(FEATURE_NAMES[i] for i in header_idx))

    source_report(X, y, "all 65 features")
    source_report(X[:, header_idx], y, "header/format features only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
