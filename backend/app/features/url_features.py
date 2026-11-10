"""Group 2: URL evidence (destinations, look-alike tricks, link text vs real target)."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.ingestion.email_parser import ParsedEmail

from . import lexicons as lx
from .common import DOMAIN_TOKEN_RE, IP_RE, ExtractionContext, registered_domain, scale_days, split_host

GROUP = "url"
NAMES = [
    "url_count", "unique_domain_count", "link_text_mismatch", "link_text_mismatch_count", "ip_in_host",
    "uses_shortener", "punycode", "max_subdomain_depth", "max_url_length", "max_path_depth", "has_port",
    "percent_encoding_ratio", "special_char_ratio", "brand_in_subdomain_or_path", "suspicious_tld", "http_only",
    "landing_domain_age_days", "landing_domain_age_missing",
]


def extract(p: ParsedEmail, ctx: ExtractionContext) -> tuple[dict[str, float], dict]:
    mism: list[dict] = []
    ip_hosts: list[str] = []
    shorteners: list[str] = []
    puny: list[str] = []
    brand_hits: list[dict] = []
    bad_tlds: list[str] = []
    http_urls: list[str] = []
    domains: set[str] = set()
    max_depth = 0
    max_len = 0
    max_special = 0.0
    max_path = 0
    port_hit = False
    max_encoded = 0.0

    for link in p.links:
        parsed = urlparse(link.href)
        host, reg, sub = split_host(link.href)
        if not host:
            continue
        domains.add(reg)
        max_depth = max(max_depth, len([s for s in sub.split(".") if s]))
        max_len = max(max_len, len(link.href))
        special = len(re.findall(r"[@%\-_=&~]", link.href)) / max(1, len(link.href))
        max_special = max(max_special, special)
        path_segments = [s for s in parsed.path.split("/") if s]
        max_path = max(max_path, len(path_segments))
        try:
            port = parsed.port
        except ValueError:  # unparseable or out-of-range port in a hostile href
            port = -1
        if port is not None and port not in (80, 443):
            port_hit = True
        encoded = len(re.findall(r"%[0-9a-f]{2}", link.href, re.I)) / max(1, len(link.href))
        max_encoded = max(max_encoded, encoded)
        if IP_RE.match(host):
            ip_hosts.append(host)
        if reg in lx.URL_SHORTENERS:
            shorteners.append(reg)
        if "xn--" in host:
            puny.append(host)
        tld = reg.rsplit(".", 1)[-1] if "." in reg else ""
        if tld in lx.SUSPICIOUS_TLDS:
            bad_tlds.append(reg)
        if link.href.lower().startswith("http://"):
            http_urls.append(link.href)
        hay = f"{sub}.{link.href.split('//', 1)[-1].split('/', 1)[-1].lower()}"
        for brand, legit in lx.BRANDS.items():
            if brand in hay and reg not in legit:
                brand_hits.append({"brand": brand, "domain": reg})
                break
        # link text that itself looks like a different domain than the real destination
        m = DOMAIN_TOKEN_RE.search(link.text or "")
        if m:
            shown = registered_domain(m.group(1).lower())
            if shown and shown != reg:
                mism.append({"shown": shown, "actual": reg})

    ages = [ctx.domain_age.age_days(d) for d in list(domains)[:5]]
    known = [a for a in ages if a is not None]
    f = {
        "url_count": min(len(p.links), 20) / 20.0,
        "unique_domain_count": min(len(domains), 10) / 10.0,
        "link_text_mismatch": float(bool(mism)),
        "link_text_mismatch_count": min(len(mism), 5) / 5.0,
        "ip_in_host": float(bool(ip_hosts)),
        "uses_shortener": float(bool(shorteners)),
        "punycode": float(bool(puny)),
        "max_subdomain_depth": min(max_depth, 6) / 6.0,
        "max_url_length": min(max_len, 300) / 300.0,
        "max_path_depth": min(max_path, 8) / 8.0,
        "has_port": float(port_hit),
        "percent_encoding_ratio": float(max_encoded),
        "special_char_ratio": float(max_special),
        "brand_in_subdomain_or_path": float(bool(brand_hits)),
        "suspicious_tld": float(bool(bad_tlds)),
        "http_only": float(bool(http_urls)),
        "landing_domain_age_days": scale_days(min(known) if known else 1000),
        "landing_domain_age_missing": float(not known),
    }
    ev = {"mismatches": mism[:3], "ip_hosts": ip_hosts[:3], "shorteners": shorteners[:3], "punycode": puny[:3],
          "brand_urls": brand_hits[:3], "bad_tlds": bad_tlds[:3], "http_urls": http_urls[:3],
          "landing_age": {"days": min(known) if known else None, "domain": next(iter(domains), "")},
          "domains": sorted(domains)[:10]}
    return f, ev
