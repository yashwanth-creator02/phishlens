"""The analysis pipeline: bytes in -> stored, explained result out.

    parse -> sender profile -> features -> model -> calibrated score -> SHAP -> verified reasons -> persist
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db import repository as repo
from app.db.models import Analysis, EmailRaw, Explanation, FeatureValue, new_id
from app.explain.reasons import build_reasons, fallback_reason
from app.explain.shap_engine import contributions
from app.features.common import DomainAgeProvider, ExtractionContext, NullDomainAge, ProfileData
from app.features.behavioral_features import update_profile
from app.features.feature_vector import FEATURE_GROUP, FEATURE_NAMES, extract_all
from app.ingestion.email_parser import parse_email
from app.ml.registry import ModelBundle
from app.scoring.risk_bands import band_for, to_score


@dataclass
class BaselineResult:
    sender: str
    message_count: int


def _store_raw(settings: Settings, user_id: str, analysis_id: str, raw: bytes) -> str:
    d = Path(settings.storage_dir) / user_id
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{analysis_id}.eml"
    path.write_bytes(raw)
    return str(path)


def add_baseline(db: Session, settings: Settings, user_id: str, raw: bytes,
                 now: datetime | None = None) -> BaselineResult:
    """Record a KNOWN-GOOD email so that future emails from the same sender can be compared with it."""
    now = now or datetime.utcnow()
    parsed = parse_email(raw)
    sender = parsed.from_addr or "unknown"
    prof = repo.load_profile(db, user_id, sender) or ProfileData()
    ctx = ExtractionContext(profile=prof, min_history=settings.min_history_messages, now=now)
    fx = extract_all(parsed, ctx)
    prof = update_profile(prof, parsed, fx.urgency, fx.link_domains, now)
    repo.save_profile(db, user_id, sender, prof)
    db.commit()
    return BaselineResult(sender=sender, message_count=prof.message_count)


def analyze(db: Session, settings: Settings, bundle: ModelBundle, user_id: str, raw: bytes,
            domain_age: DomainAgeProvider | None = None, now: datetime | None = None) -> Analysis:
    now = now or datetime.utcnow()
    parsed = parse_email(raw)
    sender = parsed.from_addr or "unknown"
    profile = repo.load_profile(db, user_id, sender)
    ctx = ExtractionContext(domain_age=domain_age or NullDomainAge(), profile=profile,
                            min_history=settings.min_history_messages, now=now)
    fx = extract_all(parsed, ctx)

    p_raw, p_cal = bundle.predict(fx.vector)
    score = to_score(p_cal)
    band = band_for(score, settings.band_low_max, settings.band_high_min)
    contribs = contributions(bundle, fx.vector)
    min_c = bundle.meta.get("reason_min_contribution", settings.min_reason_contribution)
    reasons = build_reasons(contribs, fx.values, fx.evidence, settings.top_k_reasons, min_c)
    if band != "LOW" and not reasons:
        reasons = [fallback_reason()]

    aid = new_id()
    a = Analysis(
        id=aid, user_id=user_id, created_at=now, sender_address=sender, sender_name=parsed.from_name,
        subject=parsed.subject, scope=parsed.scope, forwarded_by=parsed.forwarded_by, probability=p_cal,
        risk_score=score, risk_band=band, model_version=bundle.version_tag, auth=parsed.auth, evidence=fx.evidence)
    a.raw = EmailRaw(
        analysis_id=aid, storage_path=_store_raw(settings, user_id, aid, raw), sha256=parsed.raw_sha256,
        headers=parsed.headers, text_preview=parsed.text_body[:2000],
        links=[{"href": l.href, "text": l.text} for l in parsed.links[:50]],
        attachments=[{"filename": x.filename, "content_type": x.content_type, "size": x.size, "sha256": x.sha256}
                     for x in parsed.attachments])
    a.features = [FeatureValue(analysis_id=aid, name=n, group=FEATURE_GROUP[n], value=v, contribution=contribs.get(n, 0.0))
                  for n, v in zip(FEATURE_NAMES, fx.vector)]
    a.explanations = [Explanation(analysis_id=aid, rank=r.rank, rule_key=r.rule_key, group=r.group,
                                  contribution=r.contribution, sentence=r.sentence) for r in reasons]
    db.add(a)

    # Learn the sender's normal behaviour ONLY from messages that look safe (never from MEDIUM/HIGH).
    if band == "LOW":
        prof = profile or ProfileData()
        prof = update_profile(prof, parsed, fx.urgency, fx.link_domains, now)
        repo.save_profile(db, user_id, sender, prof)
    db.commit()
    return a
