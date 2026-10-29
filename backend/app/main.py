from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyses, webhooks
from app.core.config import get_settings
from app.db.repository import sync_model_version
from app.db.session import get_sessionmaker, init_db
from app.ml.registry import ModelNotAvailable, load_active

VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    init_db()
    try:
        bundle = load_active(settings.model_dir)
        with get_sessionmaker()() as db:
            sync_model_version(db, bundle.meta)
    except ModelNotAvailable:
        pass  # the API still starts; /api/health reports model_loaded=false
    yield


app = FastAPI(title="PhishLens API", version=VERSION, lifespan=lifespan,
              description="Explainable phishing detection: forward an email, get a risk level and reasons.")
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(analyses.router)
app.include_router(webhooks.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    try:
        b = load_active(get_settings().model_dir)
        return {"status": "ok", "version": VERSION, "model_loaded": True, "model": b.version_tag,
                "auth_mode": get_settings().auth_mode}
    except ModelNotAvailable as exc:
        return {"status": "degraded", "version": VERSION, "model_loaded": False, "detail": str(exc),
                "auth_mode": get_settings().auth_mode}
