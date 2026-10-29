#!/usr/bin/env python3
"""Post a sample .eml to the running API's inbound webhook, as an email provider would.

    python scripts/send_sample.py backend/data/sample_emails/phish_paypal_direct.eml \
        --alias u-1a2b3c4d@phishlens.example --secret change-me
(get your alias from the Settings page or GET /api/me/alias)"""
import argparse
import urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("eml")
ap.add_argument("--alias", required=True)
ap.add_argument("--secret", default="change-me")
ap.add_argument("--url", default="http://localhost:8000/api/webhooks/inbound")
a = ap.parse_args()
req = urllib.request.Request(a.url, data=open(a.eml, "rb").read(), method="POST", headers={
    "Content-Type": "message/rfc822", "X-Webhook-Secret": a.secret, "X-Recipient": a.alias})
print(urllib.request.urlopen(req).read().decode())
