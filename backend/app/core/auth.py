"""Caller identity and email-confirmation checks.

An account may only hold a forwarding alias once its email address is confirmed.
The check calls Supabase's own ``GET /auth/v1/user`` with the caller's own access
token, so no service-role key is involved: the token proves who is asking and the
response says whether the address was confirmed.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.config import Settings

# The confirmation state rarely changes; a short cache keeps the alias endpoint
# from calling Supabase on every page load.
CACHE_TTL_SECONDS = 300
_TIMEOUT_SECONDS = 5


@dataclass(frozen=True)
class Principal:
    """The authenticated caller: who they are, and the token that proves it."""
    id: str
    email: str
    token: str


_cache: dict[str, tuple[float, bool]] = {}


def clear_cache() -> None:
    _cache.clear()


def _supabase_user(token: str, settings: Settings) -> dict:
    """Read the caller's own Supabase user record. Raises 503 when it cannot be read."""
    base = settings.supabase_api_base
    if not base or not settings.supabase_anon_key:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Email verification is not configured")
    request = urllib.request.Request(
        f"{base}/auth/v1/user",
        headers={"Authorization": f"Bearer {token}", "apikey": settings.supabase_anon_key},
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        # Fail closed: an unreachable Supabase must not look like a confirmed address.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE,
                            "Could not verify the email address") from exc


def is_email_verified(principal: Principal, settings: Settings) -> bool:
    """True when the account's email address is confirmed.

    ``auth_mode == "disabled"`` is the local single-user mode; it has no external
    identity to check, so it counts as verified.
    """
    if settings.auth_mode == "disabled":
        return True
    if not principal.email:
        return False
    now = time.monotonic()
    cached = _cache.get(principal.id)
    if cached is not None and cached[0] > now:
        return cached[1]
    payload = _supabase_user(principal.token, settings)
    verified = bool(payload.get("email_confirmed_at") or payload.get("confirmed_at"))
    _cache[principal.id] = (now + CACHE_TTL_SECONDS, verified)
    return verified
