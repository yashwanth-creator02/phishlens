from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import active_model, current_user
from app.api.limits import MAX_MESSAGE_BYTES
from app.core.config import Settings, get_settings
from app.db import repository as repo
from app.db.models import Analysis
from app.db.session import get_db
from app.ml.registry import ModelBundle
from app.schemas import (AliasOut, AnalysisDetail, AnalysisList, AnalysisSummary, AttachmentOut, BaselineOut,
                         FeatureOut, ModelInfo, PurgeOut, ReasonOut)
from app.scoring.risk_bands import GUIDANCE
from app.services import analysis_service

router = APIRouter(prefix="/api", tags=["analyses"])
CHUNK_SIZE = 1024 * 1024


async def _read(upload: UploadFile) -> bytes:
    data = bytearray()
    while chunk := await upload.read(CHUNK_SIZE):
        data.extend(chunk)
        if len(data) > MAX_MESSAGE_BYTES:
            raise HTTPException(413, "File too large (limit 10 MB)")
    if not data:
        raise HTTPException(400, "Empty file")
    return bytes(data)


def _detail(db: Session, a: Analysis) -> AnalysisDetail:
    prof = repo.load_profile(db, a.user_id, a.sender_address)
    return AnalysisDetail(
        id=a.id, created_at=a.created_at, sender_address=a.sender_address, sender_name=a.sender_name,
        subject=a.subject, scope=a.scope, risk_score=a.risk_score, risk_band=a.risk_band,
        model_version=a.model_version, probability=a.probability, forwarded_by=a.forwarded_by, auth=a.auth,
        guidance=GUIDANCE[a.risk_band],
        reasons=[ReasonOut(rank=e.rank, rule_key=e.rule_key, group=e.group, contribution=e.contribution,
                           sentence=e.sentence) for e in a.explanations],
        links=a.raw.links if a.raw else [],
        attachments=[AttachmentOut(**x) for x in (a.raw.attachments if a.raw else [])],
        text_preview=a.raw.text_preview if a.raw else "", headers=a.raw.headers if a.raw else {},
        history_message_count=prof.message_count if prof else 0)


@router.post("/analyses/upload", response_model=AnalysisDetail)
async def upload_eml(file: UploadFile = File(...), user: str = Depends(current_user),
                     db: Session = Depends(get_db), settings: Settings = Depends(get_settings),
                     bundle: ModelBundle = Depends(active_model)) -> AnalysisDetail:
    """Analyse an .eml file (used by the web UI's upload box and by developers)."""
    raw = await _read(file)
    a = analysis_service.analyze(db, settings, bundle, user, raw)
    return _detail(db, a)


@router.post("/baseline", response_model=BaselineOut)
async def upload_baseline(file: UploadFile = File(...), user: str = Depends(current_user),
                          db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> BaselineOut:
    """Upload a KNOWN-GOOD email so later emails from the same sender can be compared with it."""
    raw = await _read(file)
    res = analysis_service.add_baseline(db, settings, user, raw)
    return BaselineOut(sender=res.sender, message_count=res.message_count,
                       note="Sender history updated. Behavioural checks start after "
                            f"{settings.min_history_messages} messages.")


@router.get("/analyses", response_model=AnalysisList)
def list_analyses(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                  user: str = Depends(current_user), db: Session = Depends(get_db)) -> AnalysisList:
    q = select(Analysis).where(Analysis.user_id == user).order_by(Analysis.created_at.desc())
    total = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.user_id == user)) or 0
    rows = db.scalars(q.limit(limit).offset(offset)).all()
    return AnalysisList(items=[AnalysisSummary.model_validate(r, from_attributes=True) for r in rows], total=total)


def _own(db: Session, user: str, aid: str) -> Analysis:
    a = db.get(Analysis, aid)
    if a is None or a.user_id != user:
        raise HTTPException(404, "Analysis not found")
    return a


@router.get("/analyses/{aid}", response_model=AnalysisDetail)
def get_analysis(aid: str, user: str = Depends(current_user), db: Session = Depends(get_db)) -> AnalysisDetail:
    return _detail(db, _own(db, user, aid))


@router.get("/analyses/{aid}/features", response_model=list[FeatureOut])
def get_features(aid: str, user: str = Depends(current_user), db: Session = Depends(get_db)) -> list[FeatureOut]:
    a = _own(db, user, aid)
    return [FeatureOut(name=f.name, group=f.group, value=f.value, contribution=f.contribution)
            for f in sorted(a.features, key=lambda f: -abs(f.contribution))]


@router.delete("/analyses/{aid}", status_code=204)
def delete_analysis(aid: str, user: str = Depends(current_user), db: Session = Depends(get_db)) -> None:
    # _own() raises 404 for missing or other-user rows, so the service only runs for owned rows.
    _own(db, user, aid)
    if analysis_service.delete_analysis(db, user, aid) is False:
        raise HTTPException(404, "Analysis not found")


@router.post("/admin/purge", response_model=PurgeOut)
def purge_old(x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
              db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> PurgeOut:
    """Purge analyses older than retention_days. Guarded by admin_token (not a user JWT)."""
    if not settings.admin_token:
        raise HTTPException(503, "Admin purge is disabled (PHISHLENS_ADMIN_TOKEN is empty)")
    if x_admin_token != settings.admin_token:
        raise HTTPException(401, "Invalid admin token")
    before = datetime.utcnow() - timedelta(days=settings.retention_days)
    deleted = analysis_service.purge_expired(db, before)
    return PurgeOut(deleted=deleted)


@router.get("/me/alias", response_model=AliasOut)
def my_alias(user: str = Depends(current_user), db: Session = Depends(get_db),
             settings: Settings = Depends(get_settings)) -> AliasOut:
    row = repo.get_or_create_alias(db, user)
    return AliasOut(address=f"u-{row.token}@{settings.alias_domain}", token=row.token)


@router.get("/model", response_model=ModelInfo)
def model_info(bundle: ModelBundle = Depends(active_model)) -> ModelInfo:
    m = bundle.meta
    return ModelInfo(version_tag=m["version_tag"], algorithm=m["algorithm"], trained_at=m.get("trained_at"),
                     metrics=m.get("metrics", {}), data_source=m.get("data_source", "unknown"),
                     n_features=len(m["feature_names"]))
