"""Storage service for raw .eml message payloads.

Supports both local filesystem storage (development/testing) and remote
Supabase Storage bucket 'raw_emails' (production/cloud).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import urllib.error
import urllib.request

from ..core.config import Settings

logger = logging.getLogger(__name__)


def _write_local(storage_dir: str, user_id: str, analysis_id: str, raw: bytes) -> Path:
    """Write raw bytes to local filesystem storage."""
    d = Path(storage_dir) / user_id
    d.mkdir(parents=True, exist_ok=True)
    target = d / f"{analysis_id}.eml"
    target.write_bytes(raw)
    return target


def store_raw_email(
    settings: Settings,
    user_id: str,
    analysis_id: str,
    raw: bytes,
    user_token: str | None = None,
) -> str:
    """Store raw email bytes in Supabase Storage when configured, with local fallback.

    Object path: <user_id>/<analysis_id>.eml in bucket <supabase_storage_bucket>.
    Returns storage identifier (e.g. 'supabase://raw_emails/<user_id>/<analysis_id>.eml'
    or local filepath).
    """
    # Always write to local storage as local cache/fallback
    local_path = _write_local(settings.storage_dir, user_id, analysis_id, raw)

    token = settings.supabase_service_role_key or user_token
    if not (settings.auth_mode == "supabase" and token and settings.supabase_url):
        return str(local_path)

    bucket = settings.supabase_storage_bucket or "raw_emails"
    object_key = f"{user_id}/{analysis_id}.eml"
    upload_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{object_key}"

    req = urllib.request.Request(
        upload_url,
        data=raw,
        headers={
            "apikey": settings.supabase_service_role_key or settings.supabase_anon_key,
            "Authorization": f"Bearer {token}",
            "Content-Type": "message/rfc822",
            "x-upsert": "true",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                return f"supabase://{bucket}/{object_key}"
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        logger.warning("Supabase storage upload failed, using local copy: %s", exc)

    return str(local_path)


def delete_raw_email(
    settings: Settings,
    storage_path: str,
    user_token: str | None = None,
) -> None:
    """Delete a raw email from Supabase Storage and/or local filesystem."""
    if not storage_path:
        return

    if storage_path.startswith("supabase://"):
        # Format: supabase://<bucket>/<object_key>
        parts = storage_path[len("supabase://"):].split("/", 1)
        if len(parts) == 2:
            bucket, object_key = parts
            token = settings.supabase_service_role_key or user_token
            if token and settings.supabase_url:
                del_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}"
                body = json.dumps({"prefixes": [object_key]}).encode("utf-8")
                req = urllib.request.Request(
                    del_url,
                    data=body,
                    headers={
                        "apikey": settings.supabase_service_role_key or settings.supabase_anon_key,
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    method="DELETE",
                )
                try:
                    with urllib.request.urlopen(req, timeout=10):
                        pass
                except Exception as exc:
                    logger.warning("Supabase storage delete failed for %s: %s", storage_path, exc)

            # Also delete matching local cached file if present
            local_target = Path(settings.storage_dir) / object_key
            local_target.unlink(missing_ok=True)
            return

    # Local file path
    Path(storage_path).unlink(missing_ok=True)


def purge_raw_emails(settings: Settings, storage_paths: list[str]) -> None:
    """Batch-delete raw email files across Supabase Storage and local files."""
    supabase_prefixes: dict[str, list[str]] = {}

    for path in storage_paths:
        if not path:
            continue
        if path.startswith("supabase://"):
            parts = path[len("supabase://"):].split("/", 1)
            if len(parts) == 2:
                bucket, key = parts
                supabase_prefixes.setdefault(bucket, []).append(key)
                (Path(settings.storage_dir) / key).unlink(missing_ok=True)
        else:
            Path(path).unlink(missing_ok=True)

    token = settings.supabase_service_role_key
    if not (token and settings.supabase_url and supabase_prefixes):
        return

    for bucket, keys in supabase_prefixes.items():
        # Supabase allows batch deletions up to 100 at a time
        for i in range(0, len(keys), 100):
            batch = keys[i : i + 100]
            del_url = f"{settings.supabase_url.rstrip('/')}/storage/v1/object/{bucket}"
            body = json.dumps({"prefixes": batch}).encode("utf-8")
            req = urllib.request.Request(
                del_url,
                data=body,
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="DELETE",
            )
            try:
                with urllib.request.urlopen(req, timeout=15):
                    pass
            except Exception as exc:
                logger.warning("Batch delete failed on Supabase storage %s: %s", bucket, exc)
