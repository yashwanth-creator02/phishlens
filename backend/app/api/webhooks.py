"""Inbound email webhook. Provider-agnostic: accepts either

* the raw RFC 5322 message as the request body (Content-Type: message/rfc822), with the recipient in the
  ``X-Recipient`` header, or
* JSON ``{"recipient": "...", "raw_email_b64": "<base64 of the raw message>"}``.

Protected by a shared secret (``X-Webhook-Secret``). Adapters for specific providers (Postmark, Mailgun,
SendGrid) belong in app/ingestion/ - see docs/05-backend-design.md.
"""
from __future__ import annotations

import base64
import binascii
import hmac
import json
import re

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import active_model
from app.api.limits import MAX_BASE64_BYTES, MAX_MESSAGE_BYTES
from app.core.config import Settings, get_settings
from app.db import repository as repo
from app.db.session import get_db
from app.ml.registry import ModelBundle
from app.services import analysis_service

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])
ALIAS_RE = re.compile(r"u-([0-9a-f]{8})@", re.I)


async def _read_body(request: Request, limit: int) -> bytes:
    """Read the request body without ever buffering more than `limit` bytes."""
    content_length = request.headers.get("content-length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError as exc:
            raise HTTPException(400, "Invalid Content-Length") from exc
        if declared > limit:
            raise HTTPException(400, "Empty or oversized message")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > limit:
            raise HTTPException(400, "Empty or oversized message")
        body.extend(chunk)
    return bytes(body)


@router.post("/inbound", status_code=202)
async def inbound(request: Request, x_webhook_secret: str | None = Header(default=None),
                  x_recipient: str | None = Header(default=None), db: Session = Depends(get_db),
                  settings: Settings = Depends(get_settings), bundle: ModelBundle = Depends(active_model)) -> dict:
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, settings.webhook_secret):
        raise HTTPException(401, "Bad webhook secret")
    content_type = (request.headers.get("content-type") or "").split(";", 1)[0].strip().lower()
    is_json = content_type == "application/json" or content_type.endswith("+json")
    body = await _read_body(request, MAX_BASE64_BYTES if is_json else MAX_MESSAGE_BYTES)
    recipient = x_recipient or ""
    if is_json:
        try:
            payload = json.loads(body)
            body = base64.b64decode(payload["raw_email_b64"], validate=True)
            candidate = payload.get("recipient")
            if candidate is not None:
                if not isinstance(candidate, str):
                    raise TypeError("recipient must be a string")
                recipient = candidate
        except (KeyError, TypeError, ValueError, binascii.Error) as exc:
            raise HTTPException(400, "Invalid JSON payload") from exc
    if not body or len(body) > MAX_MESSAGE_BYTES:
        raise HTTPException(400, "Empty or oversized message")
    m = ALIAS_RE.search(recipient)
    user_id = repo.user_for_alias_token(db, m.group(1).lower()) if m else None
    if user_id is None:
        raise HTTPException(404, "Unknown recipient alias")
    a = analysis_service.analyze(db, settings, bundle, user_id, body)
    return {"status": "analysed", "analysis_id": a.id, "risk_score": a.risk_score, "risk_band": a.risk_band}
