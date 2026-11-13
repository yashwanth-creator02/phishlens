"""Checks that the reasons match what the model actually used.

A reason is a sentence about the email. It is only worth reading if the features it cites are what moved
the score, and a score that swings on a knife-edge of one feature is not a measurement. These two checks
say so with numbers instead of assertion.

Neither check is a proof. The deletion test measures how much of the score the cited features account
for, and the stability test measures how much the score moves when the message is perturbed.
"""
from __future__ import annotations

import numpy as np

from app.features.feature_vector import FEATURE_NAMES
from app.ml.registry import ModelBundle


def reference_values(bundle: ModelBundle) -> np.ndarray:
    """The value each feature takes when it says nothing: the mean of the model's own background sample.

    Using the model's background rather than zero matters: for a feature where most mail is 1, zero is not
    a neutral value but a strong statement.
    """
    if bundle.background is not None and len(bundle.background):
        return np.asarray(bundle.background, dtype=float).mean(axis=0)
    return np.zeros(len(FEATURE_NAMES))


def deletion_check(bundle: ModelBundle, vector: list[float], cited_features: list[str],
                   n_random: int = 10, seed: int = 7) -> dict:
    """Replace the cited features with their reference values and re-score.

    A faithful reason names features that moved the score towards phishing, so removing them must lower
    the phishing probability.

    The drop is measured on the model's raw probability, not the calibrated one: the isotonic calibrator
    is a step function, so a saturated message stays at 1.0 whatever is done to it and the calibrated
    number cannot resolve a change at all.

    The drop is also compared with random feature sets of the same size. A score that rests on a knife
    edge can be moved by deleting almost anything, and a saturated score can be moved by nothing at all,
    so the cited features only mean something if they matter more than a random pick.
    """
    x = np.asarray([vector], dtype=float)
    ref = reference_values(bundle)
    idx = [FEATURE_NAMES.index(f) for f in cited_features if f in FEATURE_NAMES]
    raw_before, cal_before = bundle.predict(x[0].tolist())

    def drop_with(dropped_idx: list[int]) -> tuple[float, float]:
        deleted = x.copy()
        deleted[0, dropped_idx] = ref[dropped_idx]
        raw_after, cal_after = bundle.predict(deleted[0].tolist())
        return float(raw_before - raw_after), float(cal_before - cal_after)

    drop, cal_drop = drop_with(idx)
    rng = np.random.default_rng(seed)
    random_drops = []
    for _ in range(n_random):
        pick = rng.choice(len(FEATURE_NAMES), size=len(idx), replace=False).tolist()
        random_drops.append(drop_with(pick)[0])
    random_mean = float(np.mean(random_drops)) if random_drops else 0.0
    random_max = float(np.max(random_drops)) if random_drops else 0.0
    return {
        "n_features": len(idx),
        "raw_before": float(raw_before),
        "raw_after": float(raw_before - drop),
        "drop": drop,
        "calibrated_before": float(cal_before),
        "calibrated_drop": cal_drop,
        "random_drop_mean": random_mean,
        "random_drop_max": random_max,
        # The test has power only when deleting a random set of features actually moves the score. A
        # saturated score is pinned at 1.0 and cannot be moved by anything, so a comparison against
        # random features would say nothing about the reasons. Reporting a pass there would be a false
        # reassurance.
        "has_power": bool(random_max > 0.01),
    }


def band_of(bundle: ModelBundle, vector: list[float], low_max: int = 29,
            high_min: int = 70) -> tuple[str, int]:
    """The band and the 0-100 score a feature vector lands in."""
    from app.scoring.risk_bands import band_for, to_score

    score = to_score(bundle.predict(vector)[1])
    return band_for(score, low_max, high_min), score


def stability_check(bundle: ModelBundle, vector: list[float], perturbed: list[float],
                    low_max: int = 29, high_min: int = 70) -> dict:
    """Do two versions of the same message land in the same band?

    The perturbation has to be one that leaves the message meaning the same thing: a reformatted body,
    a reordered header. Adding noise to the feature vector is not that, because a binary flag moved from
    1 to 1.01 crosses the model's split and means the opposite of what it meant.
    """
    band_before, score_before = band_of(bundle, vector, low_max, high_min)
    band_after, score_after = band_of(bundle, perturbed, low_max, high_min)
    return {
        "band_before": band_before,
        "band_after": band_after,
        "score_before": score_before,
        "score_after": score_after,
        "same_band": band_before == band_after,
    }


def cited_features(reasons) -> list[str]:
    """The features the given reasons name, in order and without duplicates."""
    from .templates import RULES

    by_key = {r.key: r for r in RULES}
    seen: list[str] = []
    for reason in reasons:
        for f in getattr(by_key.get(reason.rule_key), "features", []):
            if f not in seen:
                seen.append(f)
    return seen
