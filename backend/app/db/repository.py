"""Small data-access helpers (profiles, aliases, model versions)."""
from __future__ import annotations

import secrets
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.features.common import ProfileData

from .models import Analysis, ModelVersion, SenderProfile, UserAlias


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


def load_sender_profile(db: Session, user_id: str, sender: str) -> ProfileData:
    """Neutral defaults when the sender has no history yet (cold start)."""
    return load_profile(db, user_id, sender) or ProfileData()


def delete_analysis(db: Session, user_id: str, analysis_id: str) -> str | None:
    """Delete one analysis owned by user_id, cascade to children.

    Returns the stored file path to remove after commit, or None when
    the id is missing or belongs to another user.
    """
    row = db.get(Analysis, analysis_id)
    if row is None or row.user_id != user_id:
        return None
    storage_path = row.raw.storage_path if row.raw else None
    db.delete(row)
    db.commit()
    return storage_path


def purge_expired(db: Session, before: datetime) -> tuple[int, list[str]]:
    """Delete analyses older than `before` across all users.

    Returns (count, [storage_paths...]) — caller removes files after commit.
    """
    rows = db.scalars(select(Analysis).where(Analysis.created_at < before)).all()
    paths = [r.raw.storage_path for r in rows if r.raw]
    for row in rows:
        db.delete(row)
    if rows:
        db.commit()
    return len(rows), paths
