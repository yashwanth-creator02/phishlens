from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ReasonOut(BaseModel):
    rank: int
    rule_key: str
    group: str
    contribution: float
    sentence: str


class AnalysisSummary(BaseModel):
    id: str
    created_at: datetime
    sender_address: str
    sender_name: str
    subject: str
    scope: str
    risk_score: int
    risk_band: str
    model_version: str


class FeatureOut(BaseModel):
    name: str
    group: str
    value: float
    contribution: float


class AttachmentOut(BaseModel):
    filename: str
    content_type: str
    size: int
    sha256: str


class AnalysisDetail(AnalysisSummary):
    probability: float
    forwarded_by: str
    auth: dict
    guidance: str
    reasons: list[ReasonOut]
    links: list[dict]
    attachments: list[AttachmentOut]
    text_preview: str
    headers: dict
    history_message_count: int = 0


class AnalysisList(BaseModel):
    items: list[AnalysisSummary]
    total: int


class PurgeOut(BaseModel):
    deleted: int


class ModelInfo(BaseModel):
    version_tag: str
    algorithm: str
    trained_at: str | None = None
    metrics: dict
    data_source: str
    n_features: int


class AliasOut(BaseModel):
    address: str
    token: str


class BaselineOut(BaseModel):
    sender: str
    message_count: int
    note: str
