"""Small data-access helpers (profiles, aliases, model versions)."""
from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.common import ProfileData

from .models import ModelVersion, SenderProfile, UserAlias


def load_profile(db: Session, user_id: str, sender: str) -> ProfileData | None:
    row = db.scalar(select(SenderProfile).where(SenderProfile.user_id == user_id,
                                                SenderProfile.sender_address == sender))
    if row is None:
        return None
    s = row.stats or {}
    return ProfileData(
        message_count=row.message_count, first_seen=row.first_seen, last_seen=row.last_seen,
        urgency_mean=s.get("urgency_mean", 0.0), urgency_m2=s.get("urgency_m2", 0.0),
        reply_domains=set(s.get("reply_domains", [])), return_path_domains=set(s.get("return_path_domains", [])),
        link_domains=set(s.get("link_domains", [])), centroid=s.get("centroid"))


def save_profile(db: Session, user_id: str, sender: str, p: ProfileData) -> None:
    row = db.scalar(select(SenderProfile).where(SenderProfile.user_id == user_id,
                                                SenderProfile.sender_address == sender))
    if row is None:
        row = SenderProfile(user_id=user_id, sender_address=sender)
        db.add(row)
    row.message_count, row.first_seen, row.last_seen = p.message_count, p.first_seen, p.last_seen
    row.stats = {"urgency_mean": p.urgency_mean, "urgency_m2": p.urgency_m2,
                 "reply_domains": sorted(p.reply_domains), "return_path_domains": sorted(p.return_path_domains),
                 "link_domains": sorted(p.link_domains), "centroid": p.centroid}
    row.updated_at = datetime.utcnow()


def get_or_create_alias(db: Session, user_id: str) -> UserAlias:
    row = db.get(UserAlias, user_id)
    if row is None:
        row = UserAlias(user_id=user_id, token=secrets.token_hex(4))
        db.add(row)
        db.commit()
    return row


def user_for_alias_token(db: Session, token: str) -> str | None:
    row = db.scalar(select(UserAlias).where(UserAlias.token == token))
    return row.user_id if row else None


def sync_model_version(db: Session, meta: dict) -> None:
    """Record the serving model in model_versions and mark it active (idempotent)."""
    tag = meta["version_tag"]
    for mv in db.scalars(select(ModelVersion)):
        mv.is_active = mv.version_tag == tag
    row = db.scalar(select(ModelVersion).where(ModelVersion.version_tag == tag))
    if row is None:
        m = meta.get("metrics", {})
        db.add(ModelVersion(algorithm=meta["algorithm"], version_tag=tag, f1_macro=m.get("f1_macro", 0.0),
                            roc_auc=m.get("roc_auc", 0.0), meta=meta, is_active=True))
    db.commit()
