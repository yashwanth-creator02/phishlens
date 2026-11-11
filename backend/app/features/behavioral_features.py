"""Group 6: how unusual is this message compared with what is known about the same sender?

History comes from messages the user has marked as known-good (baseline uploads) or that were analysed and
scored LOW. It is deliberately NOT updated from messages scored MEDIUM/HIGH, so that an attacker cannot
"teach" the system a spoofed sender. Below ``min_history`` earlier messages the deviation features are 0 and
``insufficient_history`` = 1, and the explanation layer is not allowed to claim a behavioural reason.
"""
from __future__ import annotations

import math
import re
import zlib
from datetime import datetime

from app.ingestion.email_parser import ParsedEmail, domain_of

from .common import ExtractionContext, ProfileData, registered_domain, scale_days

GROUP = "behaviour"
NAMES = ["sender_seen_before", "prior_message_count", "days_since_first_seen", "new_sending_domain",
         "replyto_changed", "new_link_domain", "urgency_deviation", "text_style_distance",
         "subject_reply_without_history", "insufficient_history"]
DIM = 128
EMA_ALPHA = 0.2
REPLY_PREFIX_RE = re.compile(r"^\s*(re|fwd?|aw|sv)\s*:", re.I)


def style_vector(text: str) -> list[float]:
    """Hashed character-trigram vector (L2 normalised): a light, dependency-free text fingerprint."""
    t = " ".join(text.lower().split())[:3000]
    v = [0.0] * DIM
    for i in range(len(t) - 2):
        v[zlib.crc32(t[i:i + 3].encode()) % DIM] += 1.0
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


def cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return 1.0 - dot / (na * nb)


def extract(p: ParsedEmail, ctx: ExtractionContext, urgency: float, link_domains: set[str]) -> tuple[dict[str, float], dict]:
    prof = ctx.profile
    f = {n: 0.0 for n in NAMES}
    ev: dict = {"details": [], "message_count": prof.message_count if prof else 0}
    # A "Re:" subject from a sender we have never corresponded with is a thread-hijacking signal on its own.
    reply_prefix = float(bool(REPLY_PREFIX_RE.match(p.subject)))
    if prof is None or prof.message_count == 0:
        f["insufficient_history"] = 1.0
        f["subject_reply_without_history"] = reply_prefix
        return f, ev
    f["sender_seen_before"] = 1.0
    f["prior_message_count"] = min(prof.message_count, 50) / 50.0
    if prof.first_seen:
        f["days_since_first_seen"] = scale_days((ctx.now - prof.first_seen).days)
    if prof.message_count < ctx.min_history:
        f["insufficient_history"] = 1.0
        f["subject_reply_without_history"] = reply_prefix
        return f, ev

    rt = registered_domain(domain_of(p.return_path_addr))
    if rt and rt not in prof.return_path_domains:
        f["new_sending_domain"] = 1.0
        ev["details"].append(f"it was delivered through {rt}, which this sender has not used before")
    rp = registered_domain(domain_of(p.reply_to_addr))
    if rp and rp not in prof.reply_domains:   # a sender that never used Reply-To before and now does is a change too
        f["replyto_changed"] = 1.0
        ev["details"].append(f"replies now go to {rp}, which differs from earlier messages")
    new_links = sorted(d for d in link_domains if prof.link_domains and d not in prof.link_domains)
    if new_links:
        f["new_link_domain"] = 1.0
        ev["details"].append(f"it links to {new_links[0]}, which this sender has not linked to before")
    var = prof.urgency_m2 / max(1, prof.message_count - 1)
    std = max(math.sqrt(var), 0.15)  # floor avoids huge z-scores from tiny variance
    z = abs(urgency - prof.urgency_mean) / std
    f["urgency_deviation"] = min(z, 10.0) / 10.0
    if z >= 2.0 and urgency > prof.urgency_mean:
        ev["details"].append("it is much more urgent in tone than this sender's usual messages")
    if prof.centroid:
        d = cosine_distance(style_vector(f"{p.subject}\n{p.text_body}"), prof.centroid)
        f["text_style_distance"] = d
        if d > 0.6:
            ev["details"].append("its wording is very different from this sender's usual messages")
    return f, ev


def update_profile(prof: ProfileData, p: ParsedEmail, urgency: float, link_domains: set[str],
                   now: datetime) -> ProfileData:
    """Welford update for urgency mean/variance, EMA for the text centroid, set union for domains."""
    prof.message_count += 1
    delta = urgency - prof.urgency_mean
    prof.urgency_mean += delta / prof.message_count
    prof.urgency_m2 += delta * (urgency - prof.urgency_mean)
    prof.first_seen = prof.first_seen or now
    prof.last_seen = now
    rt = registered_domain(domain_of(p.return_path_addr))
    if rt:
        prof.return_path_domains.add(rt)
    rp = registered_domain(domain_of(p.reply_to_addr))
    if rp:
        prof.reply_domains.add(rp)
    prof.link_domains |= set(list(link_domains)[:20])
    if len(prof.link_domains) > 200:
        prof.link_domains = set(list(prof.link_domains)[:200])
    vec = style_vector(f"{p.subject}\n{p.text_body}")
    prof.centroid = vec if prof.centroid is None else [
        (1 - EMA_ALPHA) * c + EMA_ALPHA * v for c, v in zip(prof.centroid, vec)]
    return prof
