from email.message import EmailMessage

from app.ingestion.email_parser import parse_email

from .conftest import sample


def test_direct_message_fields():
    p = parse_email(sample("phish_paypal_direct.eml"))
    assert p.scope == "direct"
    assert p.from_addr == "security@paypa1-secure-login.xyz"
    assert p.reply_to_addr == "paypal.claims@gmail.com"
    assert p.auth == {"spf": "fail", "dkim": "none", "dmarc": "fail"}
    assert len(p.links) == 1
    assert p.links[0].href == "http://185.44.12.9/paypal/verify"
    assert p.links[0].text == "www.paypal.com/secure/login"


def test_inline_forward_recovers_original_sender_and_marks_auth_missing():
    p = parse_email(sample("phish_invoice_forwarded_inline.eml"))
    assert p.scope == "forward_inline"
    assert p.forwarded_by == "student@example.com"
    assert p.from_addr == "billing@docs-review-portal.icu"
    assert p.reply_to_addr == "pay.now@gmail.com"
    assert set(p.auth.values()) == {"missing"}      # original authentication cannot be recovered
    assert any("bit.ly" in l.href for l in p.links)


def test_forward_as_attachment_keeps_original_headers():
    orig = EmailMessage()
    orig["From"] = "Bank <alerts@bank.example>"
    orig["Authentication-Results"] = "mx.example.com; spf=pass; dkim=pass; dmarc=pass"
    orig["Subject"] = "Hello"
    orig.set_content("Your statement is ready.")
    outer = EmailMessage()
    outer["From"] = "me@example.com"
    outer["Subject"] = "Fwd: Hello"
    outer.set_content("check this")
    outer.add_attachment(orig)
    p = parse_email(outer.as_bytes())
    assert p.scope == "forward_attachment"
    assert p.from_addr == "alerts@bank.example"
    assert p.auth == {"spf": "pass", "dkim": "pass", "dmarc": "pass"}
    assert p.forwarded_by == "me@example.com"


def test_attachment_metadata_only():
    m = EmailMessage()
    m["From"] = "a@b.example"
    m.set_content("see file")
    m.add_attachment(b"MZ\x90fake", maintype="application", subtype="octet-stream", filename="invoice.pdf.exe")
    p = parse_email(m.as_bytes())
    assert p.attachments[0].filename == "invoice.pdf.exe"
    assert p.attachments[0].size == 7
    assert len(p.attachments[0].sha256) == 64


def test_received_spf_fallback_when_auth_results_missing():
    m = EmailMessage()
    m["From"] = "sender@legit.example"
    m["Received-SPF"] = "pass (mail.example: domain of sender@legit.example designates 1.2.3.4 as permitted sender)"
    m.set_content("Hello from legitimate sender")
    p = parse_email(m.as_bytes())
    assert p.auth["spf"] == "pass"
    assert p.auth["dkim"] == "missing"
    assert p.auth["dmarc"] == "missing"
