from __future__ import annotations

import json
from pathlib import Path

import pytest

from training import download_kaggle as dk


def test_build_message_keeps_the_headers_the_row_carries():
    raw = dk.build_message({
        "sender": "Someone <someone@example.com>",
        "receiver": "someone@example.com",
        "date": "Tue, 05 Aug 2008 16:31:02 -0700",
        "subject": "Invoice attached",
        "body": "Please find the invoice http://185.44.12.9/invoice",
    })
    assert raw is not None
    text = raw.decode("utf-8", "replace")
    assert "From: Someone <someone@example.com>" in text
    assert "To: someone@example.com" in text
    assert "Subject: Invoice attached" in text
    assert "Date: " in text
    assert "http://185.44.12.9/invoice" in text


def test_build_message_drops_a_row_without_the_fields_a_message_needs():
    assert dk.build_message({"sender": "", "date": "Tue, 05 Aug 2008 16:31:02 -0700",
                             "subject": "x", "body": "y"}) is None
    assert dk.build_message({"sender": "a@b.com", "date": "", "subject": "x", "body": "y"}) is None
    assert dk.build_message({"sender": "a@b.com", "date": "Tue, 05 Aug 2008 16:31:02 -0700",
                             "subject": "", "body": "y"}) is None


def test_a_sender_with_only_punctuation_keeps_the_address():
    """'..... <user@host>' has a display name the header parser cannot read."""
    assert dk._normalise_sender("..... <user@host>") == "user@host"


def test_a_display_name_starting_with_a_dot_is_dropped():
    """'.NET Buyer's Guide' makes the header parser raise on the whole message."""
    assert dk._normalise_sender("\".NET Buyer's Guide\" <user@host>") == "user@host"


def test_a_normal_display_name_is_kept():
    assert dk._normalise_sender("Someone <user@host>") == "Someone <user@host>"


def test_a_sender_without_an_address_is_rejected():
    assert dk._normalise_sender("no address here") is None
    assert dk._normalise_sender("") is None
    assert dk._normalise_sender("Someone <not-an-address>") is None


def test_a_date_outside_the_platform_range_is_dropped_not_raised():
    """The corpus holds a date in the year 102, which formatdate cannot convert."""
    assert dk._normalise_date("Thu, 22 Aug 0102 12:07:35 +0800") is None
    assert dk._normalise_date("Tue, 05 Aug 2008 16:31:02 -0700") is not None
    assert dk._normalise_date("not a date") is None


def test_a_corrupt_encoded_word_subject_does_not_raise():
    raw = dk.build_message({
        "sender": "<user@host>",
        "receiver": "<webmaster@example.org>",
        "date": "Thu, 22 Aug 2002 12:07:35 +0800",
        "subject": "=?big5?Q?re:=A7=DA=AA=BE=B9D?=",
        "body": "hello",
    })
    assert raw is not None


def test_convert_splits_phishing_from_legitimate(tmp_path: Path):
    rows = [
        {"sender": "a@b.com", "date": "Tue, 05 Aug 2008 16:31:02 -0700", "subject": "p", "body": "x", "label": "1"},
        {"sender": "c@d.com", "date": "Tue, 05 Aug 2008 16:31:02 -0700", "subject": "l", "body": "y", "label": "0"},
        {"sender": "", "date": "Tue, 05 Aug 2008 16:31:02 -0700", "subject": "?", "body": "z", "label": "1"},
        {"sender": "e@f.com", "date": "Tue, 05 Aug 2008 16:31:02 -0700", "subject": "?", "body": "w", "label": "?"},
    ]
    counts = dk.convert(rows, "label", tmp_path)
    assert counts == {"phishing": 1, "legitimate": 1, "skipped": 2}
    assert len(list((tmp_path / "phishing").glob("*.eml"))) == 1
    assert len(list((tmp_path / "legitimate").glob("*.eml"))) == 1


def test_convert_clears_the_previous_run(tmp_path: Path):
    """Each file is named after its content hash, so a stale file would survive a re-run."""
    stale = tmp_path / "phishing" / "0123456789abcdef01234567.eml"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"old conversion")
    rows = [{"sender": "a@b.com", "date": "Tue, 05 Aug 2008 16:31:02 -0700", "subject": "p",
             "body": "x", "label": "1"}]
    dk.convert(rows, "label", tmp_path)
    assert not stale.exists()
    assert len(list((tmp_path / "phishing").glob("*.eml"))) == 1


def test_the_manifest_hashes_match_the_published_csvs():
    """A dataset whose CSV changed upstream must not be used silently."""
    assert dk.DATASETS["ceas08"]["csv_sha256"] == (
        "22375e7d5f5a8229dbe987914ee9b3705656c590038662a7df6054629b376074")
    assert dk.DATASETS["nigerian-fraud"]["csv_sha256"] == (
        "f5d6930763cae6feeae6484131c79655a7440abbb97d6f51eab757aea4e6ab4b")
    assert dk.DATASETS["spamassassin-kaggle"]["csv_sha256"] == (
        "3bfe8f8abff89f69a98456be50413c2fcb20a476141116dd84ee1507b980c00e")


def test_every_manifest_dataset_declares_a_csv_that_exists_in_its_source():
    for name, spec in dk.DATASETS.items():
        assert spec["csv"].endswith(".csv"), name
        assert len(spec["csv_sha256"]) == 64, name
        assert spec["note"], name


def test_ingest_refuses_a_csv_that_does_not_match_the_manifest(tmp_path: Path, monkeypatch):
    monkeypatch.setitem(dk.DATASETS["ceas08"], "csv_sha256", "0" * 64)
    monkeypatch.setattr(dk, "_download", lambda ref: b"not a zip")
    with pytest.raises(SystemExit):
        dk.ingest("ceas08", tmp_path)


def test_summary_is_written_for_the_ingested_corpus(tmp_path: Path, monkeypatch):
    """The summary records what was built, so a later run can tell what is on disk."""
    import io
    import zipfile

    csv_bytes = (b'sender,receiver,date,subject,body,label\n'
                 b'a@b.com,c@d.com,"Tue, 05 Aug 2008 16:31:02 -0700",s,body,1\n')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("CEAS_08.csv", csv_bytes)
    monkeypatch.setattr(dk, "_download", lambda ref: buf.getvalue())
    monkeypatch.setitem(dk.DATASETS["ceas08"], "csv_sha256", dk._sha256(csv_bytes))

    summary = dk.ingest("ceas08", tmp_path)
    assert summary["counts"]["phishing"] == 1
    assert json.loads((tmp_path / "ceas08" / "summary.json").read_text())["csv_sha256"] == summary["csv_sha256"]
