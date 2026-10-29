"""Group 1: sender and header evidence."""
from __future__ import annotations

import re

from app.ingestion.email_parser import ParsedEmail, domain_of

from . import lexicons as lx
from .common import ExtractionContext, registered_domain, scale_days

GROUP = "header"
NAMES = [
    "spf_pass", "spf_fail", "dkim_pass", "dkim_fail", "dmarc_pass", "dmarc_fail", "auth_missing",
    "from_replyto_mismatch", "from_returnpath_mismatch", "display_name_brand_mismatch",
    "received_hops", "sender_domain_age_days", "sender_domain_age_missing",
]


def extract(p: ParsedEmail, ctx: ExtractionContext) -> tuple[dict[str, float], dict]:
    f: dict[str, float] = {}
    ev: dict = {}
    for k in ("spf", "dkim", "dmarc"):
        f[f"{k}_pass"] = float(p.auth[k] == "pass")
        f[f"{k}_fail"] = float(p.auth[k] == "fail")
    f["auth_missing"] = float(all(v == "missing" for v in p.auth.values()))
    ev["auth_failed"] = [k.upper() for k in ("spf", "dkim", "dmarc") if p.auth[k] == "fail"]

    from_reg = registered_domain(p.from_domain)
    rp_dom = domain_of(p.reply_to_addr)
    f["from_replyto_mismatch"] = float(bool(rp_dom) and registered_domain(rp_dom) != from_reg)
    ev["replyto"] = {"reply": p.reply_to_addr, "from": p.from_addr}
    rt_dom = domain_of(p.return_path_addr)
    f["from_returnpath_mismatch"] = float(bool(rt_dom) and registered_domain(rt_dom) != from_reg)
    ev["returnpath"] = {"return_path": p.return_path_addr, "from": p.from_addr}

    brand_hit = ""
    name = p.from_name.lower()
    for brand, domains in lx.BRANDS.items():
        if re.search(rf"\b{re.escape(brand)}\b", name) and from_reg not in domains:
            brand_hit = brand
            break
    f["display_name_brand_mismatch"] = float(bool(brand_hit))
    ev["brand"] = {"brand": brand_hit, "domain": from_reg}

    f["received_hops"] = min(p.received_count, 20) / 20.0
    age = ctx.domain_age.age_days(from_reg) if from_reg else None
    f["sender_domain_age_days"] = scale_days(age if age is not None else 1000)
    f["sender_domain_age_missing"] = float(age is None)
    ev["sender_age"] = {"days": age, "domain": from_reg}
    return f, ev
