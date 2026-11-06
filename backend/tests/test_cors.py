"""CORS contract: only configured origins are allowed, and a wildcard cannot be
combined with credentialed requests (Starlette would mirror the caller's origin)."""
from __future__ import annotations

import pytest

from app.core.config import Settings


def test_configured_origin_is_allowed(client):
    r = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_unknown_origin_gets_no_cors_header(client):
    r = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_wildcard_origin_is_rejected():
    with pytest.raises(ValueError, match=r"explicit origins"):
        _ = Settings(cors_origins="*").cors_origin_list
