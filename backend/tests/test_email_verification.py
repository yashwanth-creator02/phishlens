"""Email verification gates the forwarding alias.

An account may only hold a forwarding alias once its email address is confirmed,
because the alias is what puts mail into that account's history.
"""
from __future__ import annotations

import time

import jwt
import pytest
from sqlalchemy import select

from app.core import auth as auth_module
from app.core.auth import Principal
from app.core.config import Settings

SECRET = "jwt-test-secret-0123456789-abcdefghij"
BASE = "https://project.supabase.co"


def _headers(user: str) -> dict:
    token = jwt.encode({"sub": user, "email": f"{user}@example.com", "aud": "authenticated",
                        "exp": int(time.time()) + 600}, SECRET, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def supabase_client(make_client, monkeypatch):
    monkeypatch.setenv("PHISHLENS_SUPABASE_URL", BASE)
    monkeypatch.setenv("PHISHLENS_SUPABASE_ANON_KEY", "anon-test-key")
    return make_client("supabase")


def _alias_rows() -> list:
    from app.db.models import UserAlias
    from app.db.session import get_sessionmaker
    with get_sessionmaker()() as db:
        return list(db.scalars(select(UserAlias)).all())


def test_unverified_account_cannot_get_an_alias(supabase_client, monkeypatch):
    monkeypatch.setattr(auth_module, "_supabase_user",
                        lambda token, settings: {"email_confirmed_at": None})
    r = supabase_client.get("/api/me/alias", headers=_headers("user-a"))
    assert r.status_code == 403
    assert _alias_rows() == [], "a refused account must not get an alias row"


def test_verified_account_gets_an_alias(supabase_client, monkeypatch):
    monkeypatch.setattr(auth_module, "_supabase_user",
                        lambda token, settings: {"email_confirmed_at": "2026-01-01T00:00:00Z"})
    r = supabase_client.get("/api/me/alias", headers=_headers("user-a"))
    assert r.status_code == 200
    body = r.json()
    assert body["address"].startswith("u-") and body["address"].endswith("@phishlens.example")
    assert len(_alias_rows()) == 1


def test_confirmed_at_also_counts_as_verified(supabase_client, monkeypatch):
    monkeypatch.setattr(auth_module, "_supabase_user",
                        lambda token, settings: {"confirmed_at": "2026-01-01T00:00:00Z"})
    assert supabase_client.get("/api/me/alias", headers=_headers("user-a")).status_code == 200


def test_local_single_user_mode_is_treated_as_verified(client):
    r = client.get("/api/me/alias")
    assert r.status_code == 200 and r.json()["address"].startswith("u-")


def test_unconfigured_supabase_is_503_not_a_pass(make_client, monkeypatch):
    monkeypatch.setenv("PHISHLENS_SUPABASE_URL", "")
    monkeypatch.setenv("PHISHLENS_SUPABASE_JWKS_URL", "")
    c = make_client("supabase")
    r = c.get("/api/me/alias", headers=_headers("user-a"))
    assert r.status_code == 503


def test_unreachable_supabase_is_503_not_a_pass(supabase_client, monkeypatch):
    def boom(token, settings):
        raise auth_module.HTTPException(503, "Could not verify the email address")

    monkeypatch.setattr(auth_module, "_supabase_user", boom)
    assert supabase_client.get("/api/me/alias", headers=_headers("user-a")).status_code == 503


def test_the_api_base_is_derived_from_the_jwks_url():
    settings = Settings(supabase_url="", supabase_jwks_url=f"{BASE}/auth/v1/.well-known/jwks.json")
    assert settings.supabase_api_base == BASE
    assert Settings(supabase_url=f"{BASE}/", supabase_jwks_url="").supabase_api_base == BASE
    assert Settings(supabase_url="", supabase_jwks_url="").supabase_api_base == ""


def test_principal_carries_the_identity_the_token_proves():
    from app.api.deps import verify_supabase_token

    token = jwt.encode({"sub": "user-a", "email": "user-a@example.com", "aud": "authenticated",
                        "exp": int(time.time()) + 600}, SECRET, algorithm="HS256")
    principal = verify_supabase_token(token, Settings(supabase_jwt_secret=SECRET))
    assert principal == Principal(id="user-a", email="user-a@example.com", token=token)
