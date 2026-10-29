# 11 - Security and privacy

Forwarded emails are someone else's correspondence. Treat everything the system stores as sensitive.

| Risk | Mitigation in v0.1 | To do |
|---|---|---|
| Fake inbound deliveries (anyone can POST to the webhook) | shared secret (`X-Webhook-Secret`, constant-time compare); unknown alias -> 404 | provider-specific signature verification; IP allow-list; rate limit |
| Malicious attachments | **never opened, rendered or executed**; only name, type, size, SHA-256 | none (keep it that way) |
| Malicious HTML/links in the email | parsed with BeautifulSoup only to extract text/links; UI shows links as text (`<code>`), never as clickable anchors | CSP headers on the web app |
| Oversized / malformed mail | 10 MB limit; defensive parser | request timeouts, queue limits |
| Account takeover / data leaks between users | Supabase JWT verification (aud, HS256); ownership check on every read (`_own`) -> 404; RLS policies in SQL | integration test against real Supabase; asymmetric JWT verification (JWKS) |
| Raw email at rest | stored under `storage/<user>/<id>.eml` | **encrypt at rest** (Supabase Storage with bucket policies or app-level encryption); restrict file permissions |
| Retention | `scripts/purge_old.py` deletes analyses and files older than `RETENTION_DAYS` (30) ; user delete button | schedule the job; document the policy in the UI |
| Poisoning the sender history ("teaching" a spoofed sender) | history updated only from known-good uploads or LOW-risk results (ADR-007) | confirmation UI ("mark as safe") |
| Abuse / cost (flooding the bot) | size limit | per-user and per-sender rate limits, quotas |
| Secrets | `.env` not committed; `.env.example` provided; default webhook secret is `change-me` | enforce non-default secret in production start-up check |
| Model supply chain | `joblib` loads pickles: **only load models you trained** | sign model artefacts; keep `models/` out of untrusted uploads |
| Privacy in training | no third-party personal data used; user-study participants give informed consent | anonymisation script for project-collected samples; ethics approval note |

## Data handling summary
* Stored: raw email (file), parsed headers/links/attachment metadata/2000-char preview, features, SHAP values, reasons, per-sender statistics (domains, urgency stats, a hashed text fingerprint - not the text).
* Not stored: attachment contents, passwords/tokens, anything else.
* Deletion: per analysis (UI), by retention job, or by removing the user's rows.
* Local development uses SQLite and unencrypted files - never put real user mail in a development checkout.
