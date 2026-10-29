from datetime import datetime, timedelta
from email.message import EmailMessage

from app.features.behavioral_features import update_profile
from app.features.common import ExtractionContext, ProfileData
from app.features.feature_vector import FEATURE_GROUP, FEATURE_NAMES, GROUPS, extract_all
from app.ingestion.email_parser import parse_email

from .conftest import sample


def feats(raw: bytes, ctx: ExtractionContext | None = None):
    return extract_all(parse_email(raw), ctx or ExtractionContext())


def test_feature_registry_is_consistent():
    assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES)) == 57
    assert set(FEATURE_GROUP.values()) == set(GROUPS)
    assert len(GROUPS) == 6


def test_phishing_sample_triggers_expected_features():
    fx = feats(sample("phish_paypal_direct.eml"))
    v = fx.values
    assert v["link_text_mismatch"] == 1 and v["ip_in_host"] == 1 and v["http_only"] == 1
    assert v["spf_fail"] == 1 and v["dmarc_fail"] == 1
    assert v["from_replyto_mismatch"] == 1 and v["display_name_brand_mismatch"] == 1
    assert v["urgency_score"] > 0 and v["credential_phrase_flag"] == 1
    assert fx.evidence["url"]["mismatches"][0]["shown"] == "paypal.com"


def test_legit_sample_is_quiet():
    v = feats(sample("legit_newsletter.eml")).values
    assert v["link_text_mismatch"] == 0 and v["ip_in_host"] == 0 and v["spf_pass"] == 1
    assert v["from_replyto_mismatch"] == 0


def test_inline_forward_marks_authentication_missing():
    v = feats(sample("phish_invoice_forwarded_inline.eml")).values
    assert v["auth_missing"] == 1 and v["spf_fail"] == 0
    assert v["uses_shortener"] == 1 and v["requests_payment"] == 1


def test_attachment_features():
    m = EmailMessage()
    m["From"] = "a@b.example"
    m.set_content("see file")
    m.add_attachment(b"MZ", maintype="application", subtype="octet-stream", filename="invoice.pdf.exe")
    v = feats(m.as_bytes()).values
    assert v["double_extension"] == 1 and v["risky_extension"] == 1 and v["has_attachment"] == 1


def _history(n: int) -> ProfileData:
    prof = ProfileData()
    base = datetime(2026, 9, 1)
    for i in range(n):
        raw = sample("legit_newsletter.eml")
        p = parse_email(raw)
        ctx = ExtractionContext(profile=prof, now=base + timedelta(days=i))
        fx = extract_all(p, ctx)
        update_profile(prof, p, fx.urgency, fx.link_domains, ctx.now)
    return prof


def test_behaviour_needs_minimum_history():
    ctx = ExtractionContext(profile=_history(2), min_history=3)
    v = feats(sample("legit_newsletter.eml"), ctx).values
    assert v["insufficient_history"] == 1 and v["urgency_deviation"] == 0


def test_behaviour_detects_changes_for_known_sender():
    deviant = b"""From: "Medium Daily Digest" <no-reply@medium.com>
Subject: Act now
Return-Path: <bounce@evil-relay.top>
Reply-To: claims@gmail.com
Content-Type: text/html

<p>URGENT: verify your account immediately within 24 hours or it will be suspended!</p>
<p><a href="https://login-portal.top/x">Verify now</a></p>
"""
    ctx = ExtractionContext(profile=_history(5), min_history=3, now=datetime(2026, 10, 1))
    fx = feats(deviant, ctx)
    v = fx.values
    assert v["insufficient_history"] == 0 and v["sender_seen_before"] == 1
    assert v["new_sending_domain"] == 1 and v["replyto_changed"] == 1 and v["new_link_domain"] == 1
    assert v["urgency_deviation"] > 0.2
    assert len(fx.evidence["behaviour"]["details"]) >= 3
