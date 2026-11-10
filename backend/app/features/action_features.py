"""Group 4: what the message asks the reader to DO."""
from __future__ import annotations

from app.ingestion.email_parser import ParsedEmail

from . import lexicons as lx
from .common import ExtractionContext, count_hits

GROUP = "action"
NAMES = ["requests_click", "requests_credentials", "requests_payment", "requests_download",
         "requests_reply_info", "action_count"]
GENERIC_ANCHORS = ("click", "here", "verify", "login", "log in", "sign in", "confirm", "update", "review", "view")


def extract(p: ParsedEmail, ctx: ExtractionContext) -> tuple[dict[str, float], dict]:
    low = f"{p.subject}\n{p.text_body}".lower()
    click = count_hits(low, lx.CLICK_PHRASES)
    generic_anchor = [l.text for l in p.links if l.text and any(g in l.text.lower() for g in GENERIC_ANCHORS)]
    cred = count_hits(low, lx.CREDENTIAL_PHRASES)
    pay = count_hits(low, lx.PAYMENT_PHRASES)
    dl = count_hits(low, lx.DOWNLOAD_PHRASES)
    rep = count_hits(low, lx.REPLY_INFO_PHRASES)
    f = {
        "requests_click": float(bool(click or generic_anchor)),
        "requests_credentials": float(bool(cred)),
        "requests_payment": float(bool(pay)),
        "requests_download": float(bool(dl)),
        "requests_reply_info": float(bool(rep)),
        "action_count": sum(1 for v in (click or generic_anchor, cred, pay, dl, rep) if v) / 5.0,
    }
    ev = {"click": (click + generic_anchor)[:3], "credentials": cred[:3], "payment": pay[:3],
          "download": dl[:3], "reply_info": rep[:3]}
    return f, ev
