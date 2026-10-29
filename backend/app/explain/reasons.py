"""Turn SHAP contributions into the final ranked list of verified reasons."""
from __future__ import annotations

from dataclasses import dataclass

from .templates import RULES


@dataclass
class Reason:
    rank: int
    rule_key: str
    group: str
    contribution: float
    sentence: str


def build_reasons(contribs: dict[str, float], values: dict[str, float], evidence: dict[str, dict],
                  top_k: int = 5, min_contribution: float = 0.05) -> list[Reason]:
    """Rules:
    1. a rule's strength = sum of the POSITIVE (risk-raising) contributions of its features;
    2. rules below ``min_contribution`` are ignored;
    3. a rule whose evidence check fails is discarded (no unsupported statements);
    4. at most one reason per feature group first, then remaining slots are filled by strength;
    5. at most ``top_k`` reasons, strongest first.
    """
    cands = []
    for rule in RULES:
        strength = sum(max(0.0, contribs.get(f, 0.0)) for f in rule.features)
        if strength < min_contribution:
            continue
        fmt = rule.check(values, evidence)
        if fmt is None:
            continue
        cands.append((strength, rule, fmt))
    cands.sort(key=lambda c: -c[0])

    chosen, used_groups, rest = [], set(), []
    for c in cands:
        if c[1].group not in used_groups:
            chosen.append(c)
            used_groups.add(c[1].group)
        else:
            rest.append(c)
    chosen += rest
    chosen = sorted(chosen[:top_k], key=lambda c: -c[0])
    return [Reason(rank=i + 1, rule_key=r.key, group=r.group, contribution=round(s, 4),
                   sentence=r.template.format(**fmt)) for i, (s, r, fmt) in enumerate(chosen)]


def fallback_reason() -> Reason:
    """Shown when the risk is MEDIUM/HIGH but no individual rule could be verified against the email's
    evidence. Honest by construction: it claims nothing specific."""
    return Reason(rank=1, rule_key="overall_pattern", group="model", contribution=0.0,
                  sentence="The overall pattern of this message resembles phishing messages, but no single clear "
                           "warning sign could be verified. Treat it with caution.")
