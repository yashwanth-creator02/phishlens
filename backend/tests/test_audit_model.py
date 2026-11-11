"""Tests for the publish gate: backend/scripts/audit_model.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_model import audit, mailbox_domains, mailbox_subject_tokens


def _mailbox(tmp_path: Path) -> Path:
    box = tmp_path / "mailbox"
    box.mkdir()
    (box / "inbox.mbox").write_text(
        "From: someone@quora.com\n"
        "Reply-To: other@spotify.com\n"
        "Subject: Your invoice for the annual subscription renewal\n"
        "\n"
        "body\n\n"
        "From: third@famapp.in\n"
        "Subject: Weekly project retrospective document\n"
        "\n"
        "body\n\n"
    )
    return box


def test_domains_are_read_from_every_address_header(tmp_path: Path):
    domains = mailbox_domains(_mailbox(tmp_path))

    assert "quora.com" in domains
    assert "spotify.com" in domains, "a domain that appears only in Reply-To must still be found"
    assert "famapp.in" in domains


def test_rare_subject_words_are_collected_and_common_ones_are_not(tmp_path: Path):
    tokens = mailbox_subject_tokens(_mailbox(tmp_path))

    assert "retrospective" in tokens
    assert "subscription" in tokens


def test_a_clean_model_directory_passes(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {"contains_personal_data": True}}))
    (model / "model.joblib").write_bytes(b"\x00\x01\x02 binary payload without any mail text")

    report = audit(model, mailbox_domains(_mailbox(tmp_path)), set())

    assert report["clean"] is True
    assert report["findings"] == []
    assert report["trained_on_personal_data"] is True


def test_a_leaked_sender_domain_fails_the_audit(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "model.joblib").write_bytes(b"payload mentioning quora.com in plain text")

    report = audit(model, mailbox_domains(_mailbox(tmp_path)), set())

    assert report["clean"] is False
    assert any(f["kind"] == "sender_domain" for f in report["findings"])


def test_a_leaked_email_address_fails_the_audit(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "notes.txt").write_text("contact victim@quora.com for details")

    report = audit(model, mailbox_domains(_mailbox(tmp_path)), set())

    assert report["clean"] is False
    assert any(f["kind"] == "email_address" for f in report["findings"])


def test_a_leaked_subject_word_fails_the_audit(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "notes.txt").write_text("the retrospective document was long")

    report = audit(model, set(), {"retrospective"})

    assert report["clean"] is False
    assert any(f["kind"] == "subject_token" for f in report["findings"])


def test_random_binary_bytes_are_not_mistaken_for_an_address(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "model.joblib").write_bytes(b"g@L.Ak\x01\x02\x03")

    report = audit(model, set(), set())

    assert report["clean"] is True, report["findings"]


def test_a_utf16_encoded_leak_is_found(tmp_path: Path):
    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "notes.txt").write_bytes("quora.com".encode("utf-16"))

    report = audit(model, mailbox_domains(_mailbox(tmp_path)), set())

    assert report["clean"] is False
    assert any(f["kind"] == "sender_domain" for f in report["findings"])


def test_a_gzipped_leak_is_found(tmp_path: Path):
    import gzip

    model = tmp_path / "model"
    model.mkdir()
    (model / "meta.json").write_text(json.dumps({"training": {}}))
    (model / "notes.txt.gz").write_bytes(gzip.compress(b"quora.com"))

    report = audit(model, mailbox_domains(_mailbox(tmp_path)), set())

    assert report["clean"] is False
    assert any(f["kind"] == "sender_domain" for f in report["findings"])
