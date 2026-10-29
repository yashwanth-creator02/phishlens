"""Probability -> 0-100 score -> LOW / MEDIUM / HIGH band. Thresholds come from settings so they can be
retuned on validation data without a code change; the band used is stored with every analysis."""
from __future__ import annotations


def to_score(probability: float) -> int:
    return int(round(100 * max(0.0, min(1.0, probability))))


def band_for(score: int, low_max: int, high_min: int) -> str:
    if score >= high_min:
        return "HIGH"
    if score <= low_max:
        return "LOW"
    return "MEDIUM"


GUIDANCE = {
    "LOW": "No strong warning signs were found. Stay careful with links and requests.",
    "MEDIUM": "Some warning signs were found. Check with the sender through another channel before acting.",
    "HIGH": "Strong warning signs were found. Do not click links, open files or reply. Report and delete it.",
}
