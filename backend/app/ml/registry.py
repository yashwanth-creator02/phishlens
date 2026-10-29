"""Loads the serving model from <model_dir>/active/ (written by training/train.py).

Layout of a model directory:
    model.joblib        base classifier (sklearn / xgboost), used for prediction AND SHAP
    calibrator.joblib   optional isotonic calibrator mapping raw probability -> calibrated probability
    background.npy      small background sample for SHAP (linear models)
    meta.json           algorithm, version_tag, feature_names, metrics, reason_min_contribution, ...
"""
from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from app.features.feature_vector import FEATURE_NAMES


class ModelNotAvailable(RuntimeError):
    pass


@dataclass
class ModelBundle:
    model: Any
    calibrator: Any | None
    meta: dict
    background: np.ndarray | None
    _explainer: Any = field(default=None, repr=False)

    @property
    def algorithm(self) -> str:
        return self.meta["algorithm"]

    @property
    def version_tag(self) -> str:
        return self.meta["version_tag"]

    def predict(self, vector: list[float]) -> tuple[float, float]:
        x = np.asarray([vector], dtype=float)
        p_raw = float(self.model.predict_proba(x)[0, 1])
        p_cal = float(self.calibrator.predict([p_raw])[0]) if self.calibrator is not None else p_raw
        return p_raw, min(1.0, max(0.0, p_cal))


_lock = threading.Lock()
_cache: dict[str, tuple[float, ModelBundle]] = {}


def load_active(model_dir: Path) -> ModelBundle:
    d = Path(model_dir) / "active"
    meta_path = d / "meta.json"
    if not meta_path.exists():
        raise ModelNotAvailable(
            f"No trained model found in {d}. Run `make train-demo` (synthetic data) or training/train.py.")
    mtime = meta_path.stat().st_mtime
    with _lock:
        hit = _cache.get(str(d))
        if hit and hit[0] == mtime:
            return hit[1]
        meta = json.loads(meta_path.read_text())
        if meta["feature_names"] != FEATURE_NAMES:
            raise ModelNotAvailable(
                "The model was trained with a different feature set than the running code "
                "(train/serve skew). Retrain the model.")
        model = joblib.load(d / "model.joblib")
        cal = joblib.load(d / "calibrator.joblib") if (d / "calibrator.joblib").exists() else None
        bg = np.load(d / "background.npy") if (d / "background.npy").exists() else None
        bundle = ModelBundle(model=model, calibrator=cal, meta=meta, background=bg)
        _cache[str(d)] = (mtime, bundle)
        return bundle


def clear_cache() -> None:
    with _lock:
        _cache.clear()
