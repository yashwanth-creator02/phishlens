# ADR-002: Inbound email webhook first, Gmail API later

**Status:** accepted (v0.1)

## Context
The bot must receive forwarded mail. Gmail API needs OAuth consent, Pub/Sub and token refresh; a webhook provider needs an MX/route and a secret.

## Decision
Start with a provider-agnostic webhook (raw MIME or JSON+base64, shared secret). Keep Gmail API as an increment-5 alternative.

## Consequences
Fast to test (simulated with `scripts/send_sample.py`). Provider adapters are small. Real provider still to be chosen.
