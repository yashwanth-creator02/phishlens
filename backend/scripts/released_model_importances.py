"""Which features does the released model actually rely on?

The source-leak test (`scripts/source_leak_test.py`) shows the header/format
features identify which corpus a legitimate email came from. That only matters
if the released phishing model leans on those same features.

    cd backend
    python -m scripts.released_model_importances
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release" / "model"

# The features that identify a provider or an era rather than the message.
FINGERPRINT = ["received_hops", "auth_missing", "from_returnpath_mismatch", "spf_pass", "dkim_pass",
               "dmarc_pass", "spf_fail", "dkim_fail", "dmarc_fail", "from_replyto_mismatch"]


def main() -> int:
    meta = json.loads((RELEASE / "meta.json").read_text(encoding="utf-8"))
    names = meta["feature_names"]

    bundle = joblib.load(RELEASE / "model.joblib")
    model = bundle["model"] if isinstance(bundle, dict) and "model" in bundle else bundle

    imp = np.asarray(getattr(model, "feature_importances_", []), dtype=float)
    if imp.size != len(names):
        print(f"importance vector has {imp.size} entries for {len(names)} features; skipping")
        return 1

    total = imp.sum()
    order = np.argsort(imp)[::-1]
    print(f"released model: {meta['version_tag']}  algorithm={meta['algorithm']}")
    print(f"features={len(names)}  training n={meta.get('n_samples')}\n")
    print("top 15 features by gain:")
    for i in order[:15]:
        print(f"  {names[i]:30s} gain={imp[i]:.4f}  {imp[i] / total * 100:5.1f}%")

    present = [n for n in FINGERPRINT if n in names]
    share = sum(imp[names.index(n)] for n in present)
    print(f"\nprovider/era fingerprint features ({len(present)} of them) hold "
          f"{share / total * 100:.1f}% of the total gain")
    for n in present:
        idx = names.index(n)
        print(f"    {n:30s} gain={imp[idx]:.4f}  {imp[idx] / total * 100:5.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
