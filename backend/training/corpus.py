"""Load REAL labelled email corpora from disk (Nazario phishing corpus, SpamAssassin ham, Enron, ...).

Each directory holds .eml/.txt files (one email per file) and/or .mbox files. Returns Sample objects
compatible with training/synthetic.py so the same training code is used. Real corpora contain no
per-recipient sender history, so behavioural features are 'insufficient_history' here; evaluate them on
the semi-synthetic benchmark instead (see docs/08-ml-pipeline.md section 'Behavioural benchmark').
"""
from __future__ import annotations

import hashlib
import mailbox
from pathlib import Path

from app.features.common import NullDomainAge, split_host
from app.ingestion.email_parser import parse_email

from .synthetic import Sample

_ARCHIVE_SUFFIXES = {".gz", ".bz2", ".zip", ".tar", ".tgz", ".xz", ".7z"}


def _iter_raw(path: Path):
    # Corpus files are not always named with an extension (SpamAssassin uses a hash suffix),
    # so every non-archive file is a candidate and the parser decides.
    for f in sorted(path.rglob("*")):
        if f.is_dir() or f.name == "manifest.json" or f.suffix.lower() in _ARCHIVE_SUFFIXES:
            continue
        if f.name.lower().endswith("mbox"):
            for msg in mailbox.mbox(str(f)):
                yield bytes(msg)
            continue
        try:
            yield f.read_bytes()
        except OSError:
            continue


def load_dir(path: str | Path, label: int, limit: int | None = None) -> list[Sample]:
    out: list[Sample] = []
    seen_raw: set[str] = set()
    seen_msg_id: set[str] = set()
    seen_body: set[str] = set()
    for raw in _iter_raw(Path(path)):
        try:
            p = parse_email(raw)
        except Exception:
            continue
        # Dedupe by raw hash, Message-ID, and body content hash.
        msg_id = (p.headers.get("message-id") or "").strip().lower()
        body_hash = hashlib.sha256(p.text_body.encode("utf-8", errors="ignore")).hexdigest()
        if p.raw_sha256 in seen_raw or (msg_id and msg_id in seen_msg_id) or body_hash in seen_body:
            continue
        seen_raw.add(p.raw_sha256)
        if msg_id:
            seen_msg_id.add(msg_id)
        seen_body.add(body_hash)
        if label == 1:
            host = ""
            if p.links:
                h, reg, _ = split_host(p.links[0].href)
                host = reg or h
            if not host:
                host = p.from_domain or "unknown"
            group = f"phish-{host}"
        else:
            group = f"legit-{p.from_domain or 'unknown'}"   # split by sender domain
        out.append(Sample(raw=raw, label=label, group=group, profile=None, domain_age=NullDomainAge()))
        if limit and len(out) >= limit:
            break
    return out
