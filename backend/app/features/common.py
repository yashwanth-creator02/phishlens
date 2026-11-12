"""Shared helpers for feature modules."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from urllib.parse import urlparse

import tldextract

_EXTRACT = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)  # offline: bundled public-suffix snapshot
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$|^0x[0-9a-f]+$|^\[[0-9a-f:]+\]$", re.I)
DOMAIN_TOKEN_RE = re.compile(r"(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})", re.I)


def registered_domain(host_or_domain: str) -> str:
    if not host_or_domain:
        return ""
    ext = _EXTRACT(host_or_domain)
    return ext.registered_domain.lower() or host_or_domain.lower()


def split_host(url: str) -> tuple[str, str, str]:
    """Return (host, registered_domain, subdomain) for a URL.

    A hostile URL can make the parser raise: an unterminated IPv6 literal is the common case.
    Such a URL has no usable host, so it is reported as empty rather than crashing extraction.
    """
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return "", "", ""
    ext = _EXTRACT(host)
    return host, (ext.registered_domain.lower() or host), ext.subdomain.lower()


class DomainAgeProvider(Protocol):
    def age_days(self, registered_domain: str) -> int | None: ...


class NullDomainAge:
    """Default provider: no WHOIS/RDAP lookups (offline, deterministic). Returns None -> 'missing'."""

    def age_days(self, registered_domain: str) -> int | None:
        return None


@dataclass
class ProfileData:
    """Per-(user, sender) behavioural baseline. Persisted as JSON by the repository layer."""
    message_count: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    urgency_mean: float = 0.0
    urgency_m2: float = 0.0
    reply_domains: set[str] = field(default_factory=set)
    return_path_domains: set[str] = field(default_factory=set)
    link_domains: set[str] = field(default_factory=set)
    centroid: list[float] | None = None


@dataclass
class ExtractionContext:
    domain_age: DomainAgeProvider = field(default_factory=NullDomainAge)
    profile: ProfileData | None = None
    min_history: int = 3
    now: datetime = field(default_factory=datetime.utcnow)


def count_hits(text: str, phrases: list[str]) -> list[str]:
    return [p for p in phrases if p in text]


def clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def log1p(x: float) -> float:
    return math.log1p(max(0.0, x))


def scale_days(days: float) -> float:
    """Domain age in days -> roughly 0..1 (log scale; 10 years ~ 1.0)."""
    return min(1.0, math.log1p(max(0.0, days)) / math.log1p(3650))
