"""Group 3: language, tone and urgency. Wording is ONE category among six: fluent AI-written phishing
passes grammar checks, so these features are never trusted alone (see docs/08-ml-pipeline.md)."""
from __future__ import annotations

import re

from app.ingestion.email_parser import ParsedEmail

from . import lexicons as lx
from .common import ExtractionContext, clip, count_hits, log1p

GROUP = "text"
NAMES = ["urgency_score", "threat_score", "credential_phrase_flag", "financial_terms_ratio",
         "caps_ratio", "exclaim_count", "readability_score", "text_length"]
WORD_RE = re.compile(r"[A-Za-z']+")
VOWELS = re.compile(r"[aeiouy]+", re.I)


def _syllables(w: str) -> int:
    return max(1, len(VOWELS.findall(w)))


def flesch(text: str) -> float:
    words = WORD_RE.findall(text)
    sents = max(1, len(re.findall(r"[.!?]+", text)))
    if not words:
        return 50.0
    syl = sum(_syllables(w) for w in words)
    score = 206.835 - 1.015 * (len(words) / sents) - 84.6 * (syl / len(words))
    return clip(score, 0.0, 100.0)


def extract(p: ParsedEmail, ctx: ExtractionContext) -> tuple[dict[str, float], dict]:
    original = f"{p.subject}\n{p.text_body}"
    low = original.lower()
    words = WORD_RE.findall(original)
    nwords = max(1, len(words))
    urg = count_hits(low, lx.URGENCY_PHRASES)
    thr = count_hits(low, lx.THREAT_PHRASES)
    cred = count_hits(low, lx.CREDENTIAL_PHRASES)
    fin = sum(1 for w in words if w.lower() in lx.FINANCIAL_TERMS)
    letters = [c for c in original if c.isalpha()]
    caps = sum(1 for c in letters if c.isupper()) / max(1, len(letters))
    f = {
        "urgency_score": clip(len(urg) / 3.0, 0, 1),
        "threat_score": clip(len(thr) / 3.0, 0, 1),
        "credential_phrase_flag": float(bool(cred)),
        "financial_terms_ratio": clip(fin / nwords * 10, 0, 1),
        "caps_ratio": float(caps),
        "exclaim_count": min(10, original.count("!")) / 10.0,
        "readability_score": flesch(original) / 100.0,
        "text_length": min(1.0, log1p(len(words)) / 8.0),
    }
    ev = {"urgency_phrases": urg[:3], "threat_phrases": thr[:3], "credential_phrases": cred[:3]}
    return f, ev
