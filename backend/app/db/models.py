"""SQLAlchemy models. Mirrors supabase/migrations/0001_init.sql and docs/07-data-model.md.
Works on SQLite (local dev, default) and PostgreSQL (Supabase)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def new_id() -> str:
    return uuid.uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    sender_address: Mapped[str] = mapped_column(String(320), default="")
    sender_name: Mapped[str] = mapped_column(String(320), default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    scope: Mapped[str] = mapped_column(String(32), default="direct")      # forward_attachment|forward_inline|direct
    forwarded_by: Mapped[str] = mapped_column(String(320), default="")
    probability: Mapped[float] = mapped_column(Float)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_band: Mapped[str] = mapped_column(String(8), index=True)
    model_version: Mapped[str] = mapped_column(String(64))
    auth: Mapped[dict] = mapped_column(JSON, default=dict)                # spf/dkim/dmarc results
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)            # per-group evidence used for reasons

    raw: Mapped["EmailRaw"] = relationship(back_populates="analysis", cascade="all, delete-orphan", uselist=False)
    features: Mapped[list["FeatureValue"]] = relationship(cascade="all, delete-orphan")
    explanations: Mapped[list["Explanation"]] = relationship(
        cascade="all, delete-orphan", order_by="Explanation.rank")


class EmailRaw(Base):
    __tablename__ = "email_raw"
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), primary_key=True)
    storage_path: Mapped[str] = mapped_column(String(512))
    sha256: Mapped[str] = mapped_column(String(64))
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    text_preview: Mapped[str] = mapped_column(Text, default="")
    links: Mapped[list] = mapped_column(JSON, default=list)
    attachments: Mapped[list] = mapped_column(JSON, default=list)
    analysis: Mapped[Analysis] = relationship(back_populates="raw")


class FeatureValue(Base):
    __tablename__ = "feature_values"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    group: Mapped[str] = mapped_column(String(16))
    value: Mapped[float] = mapped_column(Float)
    contribution: Mapped[float] = mapped_column(Float, default=0.0)       # SHAP value for this feature


class Explanation(Base):
    __tablename__ = "explanations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    rank: Mapped[int] = mapped_column(Integer)
    rule_key: Mapped[str] = mapped_column(String(48))
    group: Mapped[str] = mapped_column(String(16))
    contribution: Mapped[float] = mapped_column(Float)
    sentence: Mapped[str] = mapped_column(Text)


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    algorithm: Mapped[str] = mapped_column(String(32))
    version_tag: Mapped[str] = mapped_column(String(64), unique=True)
    f1_macro: Mapped[float] = mapped_column(Float, default=0.0)
    roc_auc: Mapped[float] = mapped_column(Float, default=0.0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    trained_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)


class SenderProfile(Base):
    __tablename__ = "sender_profiles"
    __table_args__ = (UniqueConstraint("user_id", "sender_address", name="uq_profile_user_sender"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    sender_address: Mapped[str] = mapped_column(String(320))
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    stats: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)


class UserAlias(Base):
    __tablename__ = "user_aliases"
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    token: Mapped[str] = mapped_column(String(16), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
