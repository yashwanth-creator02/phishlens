"""Reason rules: feature(s) -> verified, plain-language sentence.

Every rule has a ``check`` function that looks at the EVIDENCE extracted from the email. If the evidence
does not support the statement the rule returns None and the reason is discarded, so the system never
shows a sentence that is not backed by something actually found in the message (see docs/09-explainability.md).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

Check = Callable[[dict, dict], "dict | None"]


@dataclass(frozen=True)
class Rule:
    key: str
    group: str
    features: tuple[str, ...]
    template: str
    check: Check


def _link_mismatch(v, ev):
    mm = ev["url"]["mismatches"]
    return {"shown": mm[0]["shown"], "actual": mm[0]["actual"]} if mm else None


def _auth_failed(v, ev):
    failed = ev["header"]["auth_failed"]
    return {"checks": ", ".join(failed)} if failed else None


def _replyto(v, ev):
    r = ev["header"]["replyto"]
    return {"reply": r["reply"], "sender": r["from"]} if v["from_replyto_mismatch"] and r["reply"] else None


def _returnpath(v, ev):
    r = ev["header"]["returnpath"]
    return {"rp": r["return_path"], "sender": r["from"]} if v["from_returnpath_mismatch"] and r["return_path"] else None


def _brand_display(v, ev):
    b = ev["header"]["brand"]
    return {"brand": b["brand"].title(), "domain": b["domain"]} if v["display_name_brand_mismatch"] and b["brand"] else None


def _urgency(v, ev):
    ph = ev["text"]["urgency_phrases"] or ev["text"]["threat_phrases"]
    return {"phrase": ph[0]} if ph else None


def _credentials(v, ev):
    return {} if (v["requests_credentials"] or v["credential_phrase_flag"]) else None


def _payment(v, ev):
    return {} if v["requests_payment"] else None


def _download(v, ev):
    return {} if v["requests_download"] else None


def _reply_info(v, ev):
    return {} if v["requests_reply_info"] else None


def _ip_host(v, ev):
    h = ev["url"]["ip_hosts"]
    return {"host": h[0]} if h else None


def _shortener(v, ev):
    s = ev["url"]["shorteners"]
    return {"domain": s[0]} if s else None


def _punycode(v, ev):
    p = ev["url"]["punycode"]
    return {"host": p[0]} if p else None


def _brand_url(v, ev):
    b = ev["url"]["brand_urls"]
    return {"brand": b[0]["brand"].title(), "domain": b[0]["domain"]} if b else None


def _tld(v, ev):
    t = ev["url"]["bad_tlds"]
    return {"domain": t[0]} if t else None


def _http(v, ev):
    return {} if ev["url"]["http_urls"] else None


def _domain_age(v, ev):
    land = ev["url"]["landing_age"]
    if land["days"] is not None and land["days"] < 30:
        return {"domain": land["domain"], "days": land["days"]}
    sd = ev["header"]["sender_age"]
    if sd["days"] is not None and sd["days"] < 30:
        return {"domain": sd["domain"], "days": sd["days"]}
    return None


def _attachment(v, ev):
    a = ev["attachment"]
    if a["double"]:
        return {"what": f"{a['double'][0]} has a disguised double file extension"}
    if a["risky"]:
        return {"what": f"{a['risky'][0]} is a type of file that can run code"}
    if a["macro"]:
        return {"what": f"{a['macro'][0]} is a macro-enabled document, which can run code when opened"}
    if a["mismatch"]:
        return {"what": f"{a['mismatch'][0]} is not the type of file its name claims"}
    return None


def _behaviour(v, ev):
    if v["insufficient_history"]:
        return None
    d = ev["behaviour"]["details"]
    return {"detail": "; ".join(d[:2])} if d else None


RULES: list[Rule] = [
    Rule("link_text_mismatch", "url", ("link_text_mismatch", "link_text_mismatch_count"),
         "The link text shows {shown}, but the link actually opens {actual}.", _link_mismatch),
    Rule("auth_failed", "header", ("spf_fail", "dkim_fail", "dmarc_fail"),
         "The sender's domain could not be verified as authorised to send this message ({checks} failed).", _auth_failed),
    Rule("replyto_mismatch", "header", ("from_replyto_mismatch",),
         "Replies would go to {reply}, which is different from the sender address {sender}.", _replyto),
    Rule("returnpath_mismatch", "header", ("from_returnpath_mismatch",),
         "The technical return address ({rp}) does not match the visible sender ({sender}).", _returnpath),
    Rule("brand_display_mismatch", "header", ("display_name_brand_mismatch",),
         "The sender name suggests {brand}, but the address belongs to {domain}.", _brand_display),
    Rule("urgency", "text", ("urgency_score", "threat_score", "exclaim_count", "caps_ratio"),
         'The message pressures you to act quickly (for example "{phrase}").', _urgency),
    Rule("asks_credentials", "action", ("requests_credentials", "credential_phrase_flag"),
         "The message asks you to enter or confirm your login or account details.", _credentials),
    Rule("asks_payment", "action", ("requests_payment", "financial_terms_ratio"),
         "The message asks you to make or approve a payment.", _payment),
    Rule("asks_download", "action", ("requests_download",),
         "The message asks you to download or open a file.", _download),
    Rule("asks_reply_info", "action", ("requests_reply_info",),
         "The message asks you to reply with personal or financial information.", _reply_info),
    Rule("ip_in_host", "url", ("ip_in_host",),
         "A link uses a numeric address ({host}) instead of a normal website name.", _ip_host),
    Rule("shortener", "url", ("uses_shortener",),
         "A link uses a URL shortener ({domain}), which hides where it really leads.", _shortener),
    Rule("punycode", "url", ("punycode",),
         "A link uses look-alike characters in its address ({host}).", _punycode),
    Rule("brand_in_url", "url", ("brand_in_subdomain_or_path",),
         "A link mentions {brand} but leads to {domain}, which is not {brand}'s website.", _brand_url),
    Rule("suspicious_tld", "url", ("suspicious_tld",),
         "A link ends in an address type ({domain}) that is often used for scams.", _tld),
    Rule("http_only", "url", ("http_only",),
         "A link does not use a secure (https) connection.", _http),
    Rule("young_domain", "header", ("landing_domain_age_days", "sender_domain_age_days"),
         "The website {domain} was registered only {days} days ago.", _domain_age),
    Rule("risky_attachment", "attachment",
         ("risky_extension", "double_extension", "macro_enabled_office", "mime_extension_mismatch", "archive_attachment"),
         "The attachment {what}.", _attachment),
    Rule("behaviour_change", "behaviour",
         ("new_sending_domain", "replyto_changed", "new_link_domain", "urgency_deviation", "text_style_distance"),
         "This message differs from earlier messages from this sender: {detail}.", _behaviour),
]
