"""Load REAL labelled email corpora from disk (Nazario phishing corpus, SpamAssassin ham, Enron, ...).

Each directory holds .eml/.txt files (one email per file) and/or .mbox files. Returns Sample objects
compatible with training/synthetic.py so the same training code is used. Real corpora contain no
per-recipient sender history, so behavioural features are 'insufficient_history' here; evaluate them on
the semi-synthetic benchmark instead (see docs/08-ml-pipeline.md section 'Behavioural benchmark').
"""
from __future__ import annotations

import hashlib
import mailbox
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from app.features.common import NullDomainAge, split_host
from app.ingestion.email_parser import parse_email

from .synthetic import Sample

_ARCHIVE_SUFFIXES = {".gz", ".bz2", ".zip", ".tar", ".tgz", ".xz", ".7z"}


def parse_date(value: str | None) -> datetime | None:
    """Parse an RFC 2822 Date header into an aware UTC datetime, or None when it is absent/unparsable."""
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def parse_cli_date(value: str | None) -> datetime | None:
    """Parse an ISO date from the command line into an aware UTC datetime."""
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def in_window(sample: Sample, since: datetime | None, until: datetime | None) -> bool:
    """True when the sample carries a date inside [since, until). Undated samples never match."""
    dt = parse_date(sample.date)
    if dt is None:
        return False
    return (since is None or dt >= since) and (until is None or dt < until)


def date_range(samples: list[Sample]) -> dict:
    dates = [d for d in (parse_date(s.date) for s in samples) if d is not None]
    return {
        "dated": len(dates), "undated": len(samples) - len(dates),
        "min": min(dates).isoformat() if dates else None,
        "max": max(dates).isoformat() if dates else None,
    }


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
        out.append(Sample(raw=raw, label=label, group=group, profile=None, domain_age=NullDomainAge(), date=p.date))
        if limit and len(out) >= limit:
            break
    return out


def load_mailbox(path: str | Path, label: int = 0, limit: int | None = None) -> list[Sample]:
    """Load messages from an mbox file or directory of mbox files (such as Google Takeout mailbox export),
    skipping messages labeled as Spam or Trash via X-Gmail-Labels."""
    out: list[Sample] = []
    seen_raw: set[str] = set()
    seen_msg_id: set[str] = set()
    seen_body: set[str] = set()

    mbox_path = Path(path)
    if not mbox_path.exists():
        return out

    mbox_files = [mbox_path] if mbox_path.is_file() else list(mbox_path.rglob("*.mbox"))
    for f in mbox_files:
        try:
            box = mailbox.mbox(str(f))
        except Exception:
            continue
        for msg in box:
            try:
                labels = {part.strip().lower() for part in str(msg.get("X-Gmail-Labels", "")).split(",")}
                if labels & {"spam", "trash", "sent", "drafts", "chat"}:
                    continue
                raw = bytes(msg)
                p = parse_email(raw)
            except Exception:
                continue

            msg_id = (p.headers.get("message-id") or "").strip().lower()
            body_hash = hashlib.sha256(p.text_body.encode("utf-8", errors="ignore")).hexdigest()
            if p.raw_sha256 in seen_raw or (msg_id and msg_id in seen_msg_id) or body_hash in seen_body:
                continue
            seen_raw.add(p.raw_sha256)
            if msg_id:
                seen_msg_id.add(msg_id)
            seen_body.add(body_hash)

            group = f"legit-mailbox-{p.from_domain or 'unknown'}"
            out.append(Sample(raw=raw, label=label, group=group, profile=None, domain_age=NullDomainAge(), date=p.date))
            if limit and len(out) >= limit:
                return out
    return out
