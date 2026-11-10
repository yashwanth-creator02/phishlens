import base64

from .conftest import sample, token_for


def upload(client, name, headers=None):
    return client.post("/api/analyses/upload", files={"file": (name, sample(name), "message/rfc822")}, headers=headers or {})


def test_health_reports_model(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["model_loaded"] is True


def test_phishing_is_scored_high_with_verified_reasons(client):
    r = upload(client, "phish_paypal_direct.eml")
    assert r.status_code == 200
    d = r.json()
    assert d["risk_band"] in ("MEDIUM", "HIGH") and d["risk_score"] >= 50
    assert d["reasons"], "expected at least one reason"
    text = " ".join(x["sentence"] for x in d["reasons"])
    assert "185.44.12.9" in text or "paypal" in text.lower() or "Replies would go" in text
    assert d["guidance"] and d["scope"] == "direct"
    assert d["links"][0]["href"].startswith("http://185.")


def test_legitimate_mail_is_low(client):
    for name in ("legit_newsletter.eml", "legit_bank_alert.eml"):
        d = upload(client, name).json()
        assert d["risk_band"] == "LOW", (name, d["risk_score"], [x["sentence"] for x in d["reasons"]])


def test_inline_forward_is_analysed(client):
    d = upload(client, "phish_invoice_forwarded_inline.eml").json()
    assert d["scope"] == "forward_inline" and d["forwarded_by"] == "student@example.com"
    assert d["sender_address"] == "billing@docs-review-portal.icu"
    assert d["risk_band"] in ("MEDIUM", "HIGH")


def test_list_detail_features_delete(client):
    a = upload(client, "phish_paypal_direct.eml").json()
    upload(client, "legit_newsletter.eml")
    lst = client.get("/api/analyses").json()
    assert lst["total"] == 2 and lst["items"][0]["subject"].startswith("Your weekly")   # newest first
    feats = client.get(f"/api/analyses/{a['id']}/features").json()
    assert len(feats) == 65 and abs(feats[0]["contribution"]) >= abs(feats[-1]["contribution"])
    assert client.get(f"/api/analyses/{a['id']}").json()["id"] == a["id"]
    assert client.delete(f"/api/analyses/{a['id']}").status_code == 204
    assert client.get(f"/api/analyses/{a['id']}").status_code == 404


def test_rejects_empty_upload(client):
    r = client.post("/api/analyses/upload", files={"file": ("x.eml", b"", "message/rfc822")})
    assert r.status_code == 400


def test_auth_required_and_users_are_isolated(make_client):
    c = make_client("supabase")
    assert upload(c, "phish_paypal_direct.eml").status_code == 401
    a = upload(c, "phish_paypal_direct.eml", token_for("user-a")).json()
    assert c.get(f"/api/analyses/{a['id']}", headers=token_for("user-a")).status_code == 200
    assert c.get(f"/api/analyses/{a['id']}", headers=token_for("user-b")).status_code == 404
    assert c.get("/api/analyses", headers=token_for("user-b")).json()["total"] == 0
    bad = {"Authorization": "Bearer not-a-token"}
    assert c.get("/api/analyses", headers=bad).status_code == 401


def test_webhook_requires_secret_and_known_alias(client):
    raw = sample("phish_paypal_direct.eml")
    assert client.post("/api/webhooks/inbound", content=raw).status_code == 401
    h = {"X-Webhook-Secret": "test-secret", "X-Recipient": "u-00000000@phishlens.example", "Content-Type": "message/rfc822"}
    assert client.post("/api/webhooks/inbound", content=raw, headers=h).status_code == 404
    alias = client.get("/api/me/alias").json()
    assert alias["address"].startswith("u-") and alias["address"].endswith("@phishlens.example")
    h["X-Recipient"] = alias["address"]
    r = client.post("/api/webhooks/inbound", content=raw, headers=h)
    assert r.status_code == 202 and r.json()["risk_band"] in ("MEDIUM", "HIGH")
    # JSON form
    body = {"recipient": alias["address"], "raw_email_b64": base64.b64encode(sample("legit_newsletter.eml")).decode()}
    r2 = client.post("/api/webhooks/inbound", json=body, headers={"X-Webhook-Secret": "test-secret"})
    assert r2.status_code == 202 and r2.json()["risk_band"] == "LOW"
    assert client.get("/api/analyses").json()["total"] == 2


def test_baseline_builds_history_and_high_risk_does_not_pollute_it(client):
    for _ in range(3):
        r = client.post("/api/baseline", files={"file": ("n.eml", sample("legit_newsletter.eml"), "message/rfc822")})
        assert r.status_code == 200
    assert r.json()["message_count"] == 3
    d = upload(client, "legit_newsletter.eml").json()
    assert d["history_message_count"] == 4          # LOW result is added to the sender's history
    feats = {f["name"]: f["value"] for f in client.get(f"/api/analyses/{d['id']}/features").json()}
    assert feats["insufficient_history"] == 0 and feats["sender_seen_before"] == 1
    # a HIGH-risk message from a different sender must not create/extend a profile
    h = upload(client, "phish_paypal_direct.eml").json()
    assert h["history_message_count"] == 0


def test_model_endpoint(client):
    m = client.get("/api/model").json()
    assert m["n_features"] == 65 and "synthetic" in m["data_source"]
