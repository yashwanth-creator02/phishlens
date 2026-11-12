from __future__ import annotations

import time
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "sample_emails"


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory) -> Path:
    """Train a small model once per test session (synthetic data; takes ~10 s).

    --activate is explicit: an offline training run must never replace the serving model,
    so the fixture asks for promotion the same way a deployment would.
    """
    from training import train
    d = tmp_path_factory.mktemp("models")
    train.main(["--source", "synthetic", "--n", "1400", "--out", str(d), "--reports", str(d / "reports"),
                "--activate"])
    return d


def _reset_caches():
    from app.core import auth as auth_module
    from app.core.config import get_settings
    from app.db.session import get_engine, get_sessionmaker
    from app.ml import registry
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_sessionmaker.cache_clear()
    registry.clear_cache()
    auth_module.clear_cache()


@pytest.fixture
def make_client(tmp_path, model_dir, monkeypatch):
    clients = []

    def _make(auth_mode: str = "disabled") -> TestClient:
        monkeypatch.setenv("PHISHLENS_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
        monkeypatch.setenv("PHISHLENS_STORAGE_DIR", str(tmp_path / "storage"))
        monkeypatch.setenv("PHISHLENS_MODEL_DIR", str(model_dir))
        monkeypatch.setenv("PHISHLENS_WEBHOOK_SECRET", "test-secret")
        monkeypatch.setenv("PHISHLENS_AUTH_MODE", auth_mode)
        monkeypatch.setenv("PHISHLENS_SUPABASE_JWT_SECRET", "jwt-test-secret-0123456789-abcdefghij")
        _reset_caches()
        from app.main import app
        c = TestClient(app)
        c.__enter__()
        clients.append(c)
        return c

    yield _make
    for c in clients:
        c.__exit__(None, None, None)
    _reset_caches()


@pytest.fixture
def client(make_client) -> TestClient:
    return make_client("disabled")


def token_for(user: str) -> dict:
    t = jwt.encode({"sub": user, "aud": "authenticated", "exp": int(time.time()) + 600},
                   "jwt-test-secret-0123456789-abcdefghij", algorithm="HS256")
    return {"Authorization": f"Bearer {t}"}


def sample(name: str) -> bytes:
    return (SAMPLES / name).read_bytes()
