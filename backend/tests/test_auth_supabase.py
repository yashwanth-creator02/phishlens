from __future__ import annotations

import time

import jwt
import pytest
from fastapi import HTTPException

from app.api.deps import verify_supabase_token
from app.core.config import Settings

SECRET = "jwt-test-secret-0123456789-abcdefghij"


def _token(claims: dict, secret: str = SECRET) -> str:
    return jwt.encode(claims, secret, algorithm="HS256")


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_missing_token_returns_401(make_client):
    client = make_client("supabase")
    assert client.get("/api/analyses").status_code == 401


def test_expired_token_returns_401(make_client):
    client = make_client("supabase")
    token = _token({"sub": "user-a", "aud": "authenticated", "exp": int(time.time()) - 10})
    assert client.get("/api/analyses", headers=_auth(token)).status_code == 401


def test_wrong_audience_returns_401(make_client):
    client = make_client("supabase")
    token = _token({"sub": "user-a", "aud": "other", "exp": int(time.time()) + 600})
    assert client.get("/api/analyses", headers=_auth(token)).status_code == 401


def test_valid_token_returns_user_rows(make_client):
    client = make_client("supabase")
    token = _token({"sub": "user-a", "aud": "authenticated", "exp": int(time.time()) + 600})
    response = client.get("/api/analyses", headers=_auth(token))
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_missing_subject_returns_401(make_client):
    client = make_client("supabase")
    token = _token({"aud": "authenticated", "exp": int(time.time()) + 600})
    assert client.get("/api/analyses", headers=_auth(token)).status_code == 401


def test_unconfigured_supabase_returns_401():
    settings = Settings(supabase_jwt_secret="", supabase_jwks_url="")
    with pytest.raises(HTTPException) as exc:
        verify_supabase_token("any-token", settings)
    assert exc.value.status_code == 401
