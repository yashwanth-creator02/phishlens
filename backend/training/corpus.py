"""Load REAL labelled email corpora from disk (Nazario phishing corpus, SpamAssassin ham, Enron, ...).

Each directory holds .eml/.txt files (one email per file) and/or .mbox files. Returns Sample objects
compatible with training/synthetic.py so the same training code is used. Real corpora contain no
per-recipient sender history, so behavioural features are 'insufficient_history' here; evaluate them on
the semi-synthetic benchmark instead (see docs/08-ml-pipeline.md section 'Behavioural benchmark').
"""
from __future__ import annotations

import mailbox
from pathlib import Path

from app.features.common import NullDomainAge
from app.ingestion.email_parser import parse_email

from .synthetic import Sample


def _iter_raw(path: Path):
    for f in sorted(path.rglob("*")):
        if f.is_dir():
            continue
        if f.suffix.lower() == ".mbox" or f.name.lower().endswith("mbox"):
            for msg in mailbox.mbox(str(f)):
                yield bytes(msg)
        elif f.suffix.lower() in (".eml", ".txt", ""):
            try:
                yield f.read_bytes()
            except OSError:
                continue


def load_dir(path: str | Path, label: int, limit: int | None = None) -> list[Sample]:
    out: list[Sample] = []
    seen: set[str] = set()
    for raw in _iter_raw(Path(path)):
        try:
            p = parse_email(raw)
        except Exception:
            continue
        if p.raw_sha256 in seen:            # exact-duplicate removal
            continue
        seen.add(p.raw_sha256)
        group = f"{'phish' if label else 'legit'}-{p.from_domain or 'unknown'}"   # split by sender domain
        out.append(Sample(raw=raw, label=label, group=group, profile=None, domain_age=NullDomainAge()))
        if limit and len(out) >= limit:
            break
    return out
