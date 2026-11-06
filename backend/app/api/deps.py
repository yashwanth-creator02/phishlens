from __future__ import annotations

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import Settings, get_settings
from app.ml.registry import ModelBundle, ModelNotAvailable, load_active


def verify_supabase_token(token: str, settings: Settings) -> str:
    """Return the token subject or raise 401. HS256 secret takes precedence over JWKS."""
    if settings.supabase_jwt_secret:
        key = settings.supabase_jwt_secret
        algorithms = ["HS256"]
    elif settings.supabase_jwks_url:
        try:
            jwks = jwt.PyJWKClient(settings.supabase_jwks_url)
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
    return str(sub)


def current_user(authorization: str | None = Header(default=None),
                 settings: Settings = Depends(get_settings)) -> str:
    """Return the user id. 'disabled' = single dev user; 'supabase' = verify the Supabase access token."""
    if settings.auth_mode == "disabled":
        return settings.dev_user_id
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    return verify_supabase_token(authorization.split(" ", 1)[1], settings)


def active_model(settings: Settings = Depends(get_settings)) -> ModelBundle:
    try:
        return load_active(settings.model_dir)
    except ModelNotAvailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc
