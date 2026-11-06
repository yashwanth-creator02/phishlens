# 10 - API reference

Base path `/api`. Interactive docs when running: `http://localhost:8000/docs`. Auth: `Authorization: Bearer <Supabase access token>` when `PHISHLENS_AUTH_MODE=supabase`;
in `disabled` mode every call is the single dev user.

| Method | Path | Purpose | Notes |
|---|---|---|---|
| GET | `/api/health` | status, model loaded?, auth mode | `degraded` when no model |
| GET | `/api/model` | active model: tag, algorithm, metrics, **data_source**, n_features | |
| POST | `/api/analyses/upload` | analyse an .eml (multipart field `file`) | 10 MB limit; 400 empty, 413 too large, 503 no model |
| POST | `/api/baseline` | add a **known-good** email to the sender's history | no score stored |
| GET | `/api/analyses?limit&offset` | list (newest first) | own rows only |
| GET | `/api/analyses/{id}` | detail with reasons, links, attachments, auth, preview | 404 for other users' ids |
| GET | `/api/analyses/{id}/features` | 57 features with SHAP contributions, sorted by |contribution| | |
| POST | `/api/admin/purge` | delete analyses older than `retention_days` | header `X-Admin-Token`; 503 when `PHISHLENS_ADMIN_TOKEN` is empty, 401 on mismatch |
| GET | `/api/me/alias` | personal forwarding address `u-<8 hex>@<alias_domain>` | created on first call |
| POST | `/api/webhooks/inbound` | inbound email delivery | header `X-Webhook-Secret`; see below |

## Detail response (abridged)
```json
{
  "id": "8f2e...", "created_at": "2026-10-26T08:10:00", "sender_address": "security@paypa1-secure-login.xyz",
  "sender_name": "PayPal Security", "subject": "URGENT: Your account will be suspended within 24 hours",
  "scope": "direct", "forwarded_by": "", "risk_score": 99, "risk_band": "HIGH", "probability": 0.99,
  "model_version": "xgboost-synthetic-20261026-s7",
  "guidance": "Strong warning signs were found. Do not click links, open files or reply. Report and delete it.",
  "auth": {"spf": "fail", "dkim": "none", "dmarc": "fail"},
  "reasons": [
    {"rank": 1, "rule_key": "urgency", "group": "text", "contribution": 1.206, "sentence": "The message pressures you to act quickly (for example \"immediately\")."},
    {"rank": 2, "rule_key": "link_text_mismatch", "group": "url", "contribution": 0.998, "sentence": "The link text shows paypal.com, but the link actually opens 185.44.12.9."}
  ],
  "links": [{"href": "http://185.44.12.9/paypal/verify", "text": "www.paypal.com/secure/login"}],
  "attachments": [], "text_preview": "...", "headers": {}, "history_message_count": 0
}
```

## Webhook contract (provider-agnostic)
Two accepted forms, both with `X-Webhook-Secret: <PHISHLENS_WEBHOOK_SECRET>`:
1. **Raw MIME**: body = the RFC 5322 message, `Content-Type: message/rfc822`, recipient in header `X-Recipient`.
2. **JSON**: `{"recipient": "u-1a2b3c4d@phishlens.example", "raw_email_b64": "<base64 of the raw message>"}`.

Responses: `202 {"status":"analysed","analysis_id","risk_score","risk_band"}`; `401` bad secret; `404` unknown alias; `400` empty/oversized/invalid; `503` no model.
Simulate with `scripts/send_sample.py`. For a real provider (Postmark/Mailgun/SendGrid/Cloudflare) write an adapter that converts its payload into one of these forms.

## Errors
JSON `{"detail": "..."}` with the status above. 401 for missing/invalid Supabase token (`aud=authenticated`, HS256 with the project JWT secret).
