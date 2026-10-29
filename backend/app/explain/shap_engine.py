"""Per-prediction SHAP contributions for the positive (phishing) class.

* XGBoost  -> TreeExplainer, values in log-odds (margin) units
* Random Forest -> TreeExplainer, values in probability units
* Logistic Regression -> LinearExplainer (needs the background sample), log-odds units
Contributions add up to (model output - base value); positive values push towards phishing.
"""
from __future__ import annotations

import numpy as np
import shap

from app.features.feature_vector import FEATURE_NAMES
from app.ml.registry import ModelBundle


def _explainer(bundle: ModelBundle):
    if bundle._explainer is None:
        if bundle.algorithm == "logistic_regression":
            bg = bundle.background if bundle.background is not None else np.zeros((1, len(FEATURE_NAMES)))
            bundle._explainer = shap.LinearExplainer(bundle.model, bg)
        else:
            bundle._explainer = shap.TreeExplainer(bundle.model)
    return bundle._explainer


def contributions(bundle: ModelBundle, vector: list[float]) -> dict[str, float]:
    x = np.asarray([vector], dtype=float)
    values = _explainer(bundle).shap_values(x)
    arr = np.asarray(values[1] if isinstance(values, list) else values)
    if arr.ndim == 3:           # (n, features, classes) in newer SHAP versions
        arr = arr[:, :, 1]
    row = arr[0]
    return {name: float(v) for name, v in zip(FEATURE_NAMES, row)}
