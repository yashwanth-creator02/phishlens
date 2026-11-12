from __future__ import annotations

import json
from pathlib import Path
from training import download_phishing_pot as dpp


def test_parse_message_date():
    raw_recent = b"Date: Tue, 05 Aug 2024 16:31:02 -0700\nSubject: Test\n\nbody\n"
    dt = dpp.parse_message_date(raw_recent)
    assert dt is not None
    assert dt.year == 2024

    raw_old = b"Date: Tue, 05 Aug 2020 16:31:02 -0700\nSubject: Test\n\nbody\n"
    dt_old = dpp.parse_message_date(raw_old)
    assert dt_old is not None
    assert dt_old.year == 2020

    raw_undated = b"Subject: No date\n\nbody\n"
    assert dpp.parse_message_date(raw_undated) is None


def test_process_corpus_filters_and_masks(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()

    # 1. Recent message with phishing@pot shortcut
    (src / "recent.eml").write_bytes(
        b"From: attacker@example.com\n"
        b"Date: Wed, 10 Oct 2024 10:00:00 +0000\n"
        b"Subject: Modern phishing alert\n\n"
        b"Report to phishing@pot please.\n"
    )

    # 2. Old message (year 2020 < 2022) -> should be dropped
    (src / "old.eml").write_bytes(
        b"From: attacker@example.com\n"
        b"Date: Wed, 10 Oct 2020 10:00:00 +0000\n"
        b"Subject: Old phishing\n\n"
        b"body\n"
    )

    # 3. Undated message -> should be dropped
    (src / "undated.eml").write_bytes(
        b"From: attacker@example.com\n"
        b"Subject: Undated\n\n"
        b"body\n"
    )

    dest = tmp_path / "dest"
    manifest = dpp.process_corpus(src, dest, since_year=2022)

    assert manifest["counts"]["kept"] == 1
    assert manifest["counts"]["dropped_too_old"] == 1
    assert manifest["counts"]["dropped_undated"] == 1
    assert manifest["counts"]["masked_files"] == 1

    kept_file = dest / "recent.eml"
    assert kept_file.exists()
    content = kept_file.read_bytes()
    assert b"phishing@pot" not in content
    assert b"user@example.com" in content
    assert b"Modern phishing alert" in content

    assert (dest / "manifest.json").exists()
