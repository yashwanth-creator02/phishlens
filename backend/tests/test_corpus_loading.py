"""Real corpora must load whatever the file is called.

SpamAssassin ships hash-named files ("0001.217ba49e..."), so any loader that
filters on a .eml/.txt suffix silently returns zero legitimate samples.
"""
from __future__ import annotations

from pathlib import Path

from training import corpus

HAM = (
    b"Return-Path: <someone@example.com>\r\n"
    b"Received: from mail.example.com by mx.example.com; Mon, 1 Jan 2024 10:00:00 +0000\r\n"
    b"From: Someone <someone@example.com>\r\n"
    b"Subject: lunch\r\n"
    b"Date: Mon, 1 Jan 2024 10:00:00 +0000\r\n"
    b"Message-ID: <ham-1@example.com>\r\n"
    b"\r\n"
    b"Hello, see you at noon.\r\n"
)

PHISH = (
    b"From: Alerts <security@example.net>\r\n"
    b"Subject: Verify your account\r\n"
    b"Date: Mon, 1 Jan 2024 11:00:00 +0000\r\n"
    b"Message-ID: <phish-1@example.net>\r\n"
    b"\r\n"
    b"Sign in at http://example.net/verify within 24 hours or your account closes.\r\n"
)


def test_load_dir_accepts_extensionless_hash_named_files(tmp_path: Path):
    corpus_dir = tmp_path / "spamassassin"
    (corpus_dir / "easy_ham").mkdir(parents=True)
    (corpus_dir / "easy_ham" / "0001.217ba49e4b19f7dad40f9526b1a2b1ba").write_bytes(HAM)
    (corpus_dir / "manifest.json").write_text('{"count": 1, "files": []}')

    samples = corpus.load_dir(corpus_dir, 0)

    assert len(samples) == 1, "hash-named corpus file must load, manifest must not"
    assert samples[0].label == 0
    assert samples[0].group.startswith("legit-")


def test_load_dir_reads_mbox_next_to_loose_files(tmp_path: Path):
    corpus_dir = tmp_path / "nazario"
    corpus_dir.mkdir()
    (corpus_dir / "phishing0.mbox").write_bytes(b"From sender@example.net Mon Jan  1 00:00:00 2024\n" + PHISH)
    other = (
        b"From: Billing <billing@example.org>\r\n"
        b"Subject: Invoice overdue\r\n"
        b"Date: Mon, 1 Jan 2024 12:00:00 +0000\r\n"
        b"Message-ID: <phish-2@example.org>\r\n"
        b"\r\n"
        b"Pay the attached invoice at http://example.org/pay today.\r\n"
    )
    (corpus_dir / "loose.eml").write_bytes(other)

    samples = corpus.load_dir(corpus_dir, 1)

    assert len(samples) == 2, "both the mbox message and the loose .eml must load"
    assert {s.label for s in samples} == {1}
    assert all(s.group.startswith("phish-") for s in samples)


def test_load_mailbox_filters_spam_and_trash(tmp_path: Path):
    mbox_file = tmp_path / "Takeout.mbox"

    ham_msg = (
        b"From: friend@example.com\r\n"
        b"X-Gmail-Labels: Inbox,Important\r\n"
        b"Subject: Dinner\r\n"
        b"Date: Mon, 1 Jan 2026 12:00:00 +0000\r\n"
        b"Message-ID: <ham-mail@example.com>\r\n"
        b"\r\n"
        b"See you tonight.\r\n"
    )
    spam_msg = (
        b"From: scam@example.net\r\n"
        b"X-Gmail-Labels: Spam\r\n"
        b"Subject: Win money\r\n"
        b"Date: Mon, 1 Jan 2026 13:00:00 +0000\r\n"
        b"Message-ID: <spam-mail@example.net>\r\n"
        b"\r\n"
        b"Click here.\r\n"
    )
    trash_msg = (
        b"From: ad@example.org\r\n"
        b"X-Gmail-Labels: Trash\r\n"
        b"Subject: Sale\r\n"
        b"Date: Mon, 1 Jan 2026 14:00:00 +0000\r\n"
        b"Message-ID: <trash-mail@example.org>\r\n"
        b"\r\n"
        b"Buy now.\r\n"
    )

    content = b"From sender@example.com Mon Jan  1 00:00:00 2026\n" + ham_msg + \
              b"\nFrom sender@example.net Mon Jan  1 00:00:00 2026\n" + spam_msg + \
              b"\nFrom sender@example.org Mon Jan  1 00:00:00 2026\n" + trash_msg
    mbox_file.write_bytes(content)

    samples = corpus.load_mailbox(mbox_file, label=0)
    assert len(samples) == 1, "only inbox ham must be loaded, spam and trash must be filtered out"
    assert samples[0].label == 0
    assert "friend@example.com" in samples[0].raw.decode("utf-8", errors="ignore")
