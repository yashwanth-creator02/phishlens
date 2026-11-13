from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException, status

from functools import lru_cache

from app.core.auth import Principal
from app.core.config import Settings, get_settings
from app.ml.registry import ModelBundle, ModelNotAvailable, load_active


@lru_cache(maxsize=4)
def _get_jwks_client(url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(url, cache_jwk_set=True)


def verify_supabase_token(token: str, settings: Settings) -> Principal:
    """Return the caller or raise 401. HS256 secret takes precedence over JWKS."""
    if settings.supabase_jwt_secret:
        key = settings.supabase_jwt_secret
        algorithms = ["HS256"]
    elif settings.supabase_jwks_url:
        try:
            jwks = _get_jwks_client(settings.supabase_jwks_url)
            key = jwks.get_signing_key_from_jwt(token).key
        except Exception as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
        algorithms = ["RS256", "ES256"]
    else:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Supabase auth is not configured")
    try:
        claims = jwt.decode(token, key, algorithms=algorithms, audience="authenticated")
    except jwt.PyJWTError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from exc
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token has no subject")
    return Principal(id=str(sub), email=str(claims.get("email") or ""), token=token)


def current_user(authorization: str | None = Header(default=None),
                 settings: Settings = Depends(get_settings)) -> Principal:
    """Return the caller. 'disabled' = single dev user; 'supabase' = verify the Supabase access token."""
    if settings.auth_mode == "disabled":
        return Principal(id=settings.dev_user_id, email="", token="")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return verify_supabase_token(authorization.split(" ", 1)[1], settings)


def active_model(settings: Settings = Depends(get_settings)) -> ModelBundle:
    try:
        return load_active(settings.model_dir)
    except ModelNotAvailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
