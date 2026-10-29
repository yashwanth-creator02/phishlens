from app.explain.reasons import build_reasons
from app.scoring.risk_bands import band_for, to_score


def _evidence(**over):
    ev = {
        "header": {"auth_failed": [], "replyto": {"reply": "", "from": ""}, "returnpath": {"return_path": "", "from": ""},
                   "brand": {"brand": "", "domain": ""}, "sender_age": {"days": None, "domain": ""}},
        "url": {"mismatches": [], "ip_hosts": [], "shorteners": [], "punycode": [], "brand_urls": [], "bad_tlds": [],
                "http_urls": [], "landing_age": {"days": None, "domain": ""}, "domains": []},
        "text": {"urgency_phrases": [], "threat_phrases": [], "credential_phrases": []},
        "action": {}, "attachment": {"risky": [], "double": [], "macro": [], "mismatch": [], "archive": []},
        "behaviour": {"details": [], "message_count": 0},
    }
    for k, v in over.items():
        grp, key = k.split("__")
        ev[grp][key] = v
    return ev


VALUES = {"insufficient_history": 1.0, "from_replyto_mismatch": 0.0, "from_returnpath_mismatch": 0.0,
          "display_name_brand_mismatch": 0.0, "requests_credentials": 0.0, "credential_phrase_flag": 0.0,
          "requests_payment": 0.0, "requests_download": 0.0, "requests_reply_info": 0.0}


def test_reason_without_evidence_is_discarded():
    # the model "thinks" link mismatch matters, but no mismatch evidence exists -> no sentence is produced
    out = build_reasons({"link_text_mismatch": 2.0}, VALUES, _evidence(), 5, 0.05)
    assert out == []


def test_reason_with_evidence_uses_real_values():
    ev = _evidence(url__mismatches=[{"shown": "paypal.com", "actual": "evil.top"}])
    out = build_reasons({"link_text_mismatch": 2.0}, VALUES, ev, 5, 0.05)
    assert len(out) == 1 and "paypal.com" in out[0].sentence and "evil.top" in out[0].sentence


def test_negative_contributions_never_become_reasons():
    ev = _evidence(url__mismatches=[{"shown": "a.com", "actual": "b.top"}])
    assert build_reasons({"link_text_mismatch": -1.5}, VALUES, ev, 5, 0.05) == []


def test_behaviour_reason_suppressed_on_cold_start():
    ev = _evidence(behaviour__details=["replies now go to x.com"])
    assert build_reasons({"replyto_changed": 1.0}, VALUES, ev, 5, 0.05) == []
    v2 = dict(VALUES, insufficient_history=0.0)
    assert len(build_reasons({"replyto_changed": 1.0}, v2, ev, 5, 0.05)) == 1


def test_top_k_and_group_diversity():
    ev = _evidence(url__mismatches=[{"shown": "a.com", "actual": "b.top"}], url__ip_hosts=["1.2.3.4"],
                   url__shorteners=["bit.ly"], header__auth_failed=["SPF"])
    contribs = {"link_text_mismatch": 3.0, "ip_in_host": 2.9, "uses_shortener": 2.8, "spf_fail": 1.0}
    out = build_reasons(contribs, VALUES, ev, 3, 0.05)
    assert len(out) == 3
    assert {r.group for r in out} >= {"url", "header"}    # header reason beats the 2nd/3rd url reason


def test_bands_and_scores():
    assert to_score(0.914) == 91 and to_score(-1) == 0 and to_score(2) == 100
    assert band_for(10, 29, 70) == "LOW" and band_for(29, 29, 70) == "LOW"
    assert band_for(30, 29, 70) == "MEDIUM" and band_for(69, 29, 70) == "MEDIUM"
    assert band_for(70, 29, 70) == "HIGH"


def test_fallback_reason_is_generic_and_makes_no_specific_claim():
    from app.explain.reasons import fallback_reason
    r = fallback_reason()
    assert r.rule_key == "overall_pattern" and "no single clear" in r.sentence
