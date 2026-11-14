from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

from app.core.config import Settings
from app.services.raw_storage import delete_raw_email, purge_raw_emails, store_raw_email


def test_store_raw_email_local_when_no_token(tmp_path: Path):
    settings = Settings(storage_dir=str(tmp_path), auth_mode="disabled")
    raw = b"From: user@test.com\nSubject: Test\n\nHello"
    path_str = store_raw_email(settings, "u-123", "a-456", raw)

    p = Path(path_str)
    assert p.exists()
    assert p.read_bytes() == raw
    assert "u-123" in path_str
    assert "a-456.eml" in path_str


def test_store_raw_email_supabase_success(tmp_path: Path):
    settings = Settings(
        storage_dir=str(tmp_path),
        auth_mode="supabase",
        supabase_url="https://test.supabase.co",
        supabase_storage_bucket="raw_emails",
    )
    raw = b"From: user@test.com\nSubject: Test\n\nHello"

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        res = store_raw_email(settings, "user-uuid", "analysis-uuid", raw, user_token="jwt-token")

        assert res == "supabase://raw_emails/user-uuid/analysis-uuid.eml"
        assert mock_open.called
        req = mock_open.call_args[0][0]
        assert req.full_url == "https://test.supabase.co/storage/v1/object/raw_emails/user-uuid/analysis-uuid.eml"
        assert req.headers["Authorization"] == "Bearer jwt-token"
        assert req.headers["Content-type"] == "message/rfc822"


def test_store_raw_email_supabase_failure_falls_back_to_local(tmp_path: Path):
    settings = Settings(
        storage_dir=str(tmp_path),
        auth_mode="supabase",
        supabase_url="https://test.supabase.co",
    )
    raw = b"From: user@test.com\nSubject: Test\n\nHello"

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network down")):
        res = store_raw_email(settings, "user-uuid", "analysis-uuid", raw, user_token="jwt-token")

        assert not res.startswith("supabase://")
        p = Path(res)
        assert p.exists()
        assert p.read_bytes() == raw


def test_delete_raw_email_local(tmp_path: Path):
    settings = Settings(storage_dir=str(tmp_path))
    file_path = tmp_path / "test.eml"
    file_path.write_bytes(b"data")

    delete_raw_email(settings, str(file_path))
    assert not file_path.exists()


def test_delete_raw_email_supabase(tmp_path: Path):
    settings = Settings(
        storage_dir=str(tmp_path),
        auth_mode="supabase",
        supabase_url="https://test.supabase.co",
    )
    # create a local mirror copy
    local_dir = tmp_path / "user-uuid"
    local_dir.mkdir(parents=True)
    local_file = local_dir / "analysis-uuid.eml"
    local_file.write_bytes(b"data")

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        delete_raw_email(settings, "supabase://raw_emails/user-uuid/analysis-uuid.eml", user_token="jwt-token")

        assert mock_open.called
        req = mock_open.call_args[0][0]
        assert req.method == "DELETE"
        assert not local_file.exists()


def test_purge_raw_emails_mixed(tmp_path: Path):
    settings = Settings(
        storage_dir=str(tmp_path),
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="service-key",
    )
    f1 = tmp_path / "local1.eml"
    f1.write_bytes(b"1")

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
        purge_raw_emails(settings, [
            str(f1),
            "supabase://raw_emails/u1/a1.eml",
            "supabase://raw_emails/u2/a2.eml",
        ])

        assert not f1.exists()
        assert mock_open.called
        req = mock_open.call_args[0][0]
        assert req.method == "DELETE"
