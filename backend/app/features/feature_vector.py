"""Assemble the six feature modules into one ordered vector.

THIS MODULE IS IMPORTED BY BOTH THE API AND THE TRAINING SCRIPTS. Feature logic exists exactly once
(train/serve parity, see docs/decisions/ADR-003)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.ingestion.email_parser import ParsedEmail

from . import (action_features, attachment_features, behavioral_features, header_features, text_features,
               url_features)
from .common import ExtractionContext

MODULES = [header_features, url_features, text_features, action_features, attachment_features, behavioral_features]
FEATURE_NAMES: list[str] = [n for m in MODULES for n in m.NAMES]
FEATURE_GROUP: dict[str, str] = {n: m.GROUP for m in MODULES for n in m.NAMES}
GROUPS = [m.GROUP for m in MODULES]
assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES)), "duplicate feature names"


@dataclass
class FeatureResult:
    values: dict[str, float]
    evidence: dict[str, dict]
    vector: list[float] = field(default_factory=list)
    urgency: float = 0.0
    link_domains: set[str] = field(default_factory=set)


def extract_all(p: ParsedEmail, ctx: ExtractionContext) -> FeatureResult:
    values: dict[str, float] = {}
    evidence: dict[str, dict] = {}
    for m in (header_features, url_features, text_features, action_features, attachment_features):
        f, ev = m.extract(p, ctx)
        values.update(f)
        evidence[m.GROUP] = ev
    urgency = values["urgency_score"]
    link_domains = set(evidence["url"].get("domains", []))
    f, ev = behavioral_features.extract(p, ctx, urgency, link_domains)
    values.update(f)
    evidence["behaviour"] = ev
    missing = [n for n in FEATURE_NAMES if n not in values]
    assert not missing, f"modules did not produce: {missing}"
    return FeatureResult(values=values, evidence=evidence, vector=[values[n] for n in FEATURE_NAMES],
                         urgency=urgency, link_domains=link_domains)
