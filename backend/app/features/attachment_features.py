"""Group 5: attachment metadata only. Contents are never opened, rendered or executed."""
from __future__ import annotations

import re

from app.ingestion.email_parser import ParsedEmail

from . import lexicons as lx
from .common import ExtractionContext, log1p

GROUP = "attachment"
NAMES = ["has_attachment", "attachment_count", "risky_extension", "double_extension", "macro_enabled_office",
         "mime_extension_mismatch", "archive_attachment", "max_attachment_size"]
DOUBLE_RE = re.compile(r"\.(" + "|".join(lx.DOC_EXTENSIONS) + r")\.(exe|scr|js|bat|cmd|vbs|com|jar|lnk)$", re.I)


def _ext(name: str) -> str:
    return name.rsplit(".", 1)[-1].lower() if "." in name else ""


def extract(p: ParsedEmail, ctx: ExtractionContext) -> tuple[dict[str, float], dict]:
    risky, double, macro, mism, arch = [], [], [], [], []
    for a in p.attachments:
        ext = _ext(a.filename)
        if ext in lx.RISKY_EXTENSIONS:
            risky.append(a.filename)
        if DOUBLE_RE.search(a.filename):
            double.append(a.filename)
        if ext in lx.MACRO_EXTENSIONS:
            macro.append(a.filename)
        if ext in lx.ARCHIVE_EXTENSIONS:
            arch.append(a.filename)
        exp = lx.MIME_EXPECTED.get(ext)
        if exp and a.content_type not in (exp, "application/octet-stream"):
            mism.append(a.filename)
    f = {
        "has_attachment": float(bool(p.attachments)),
        "attachment_count": min(len(p.attachments), 5) / 5.0,
        "risky_extension": float(bool(risky)),
        "double_extension": float(bool(double)),
        "macro_enabled_office": float(bool(macro)),
        "mime_extension_mismatch": float(bool(mism)),
        "archive_attachment": float(bool(arch)),
        "max_attachment_size": min(1.0, log1p(max((a.size for a in p.attachments), default=0)) / log1p(25_000_000)),
    }
    ev = {"risky": risky[:3], "double": double[:3], "macro": macro[:3], "mismatch": mism[:3], "archive": arch[:3]}
    return f, ev
