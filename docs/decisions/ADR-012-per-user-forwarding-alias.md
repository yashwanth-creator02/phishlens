# ADR-012: Per-user forwarding alias

**Status:** accepted (v0.1)

## Context
The bot inbox is not the user's mailbox, so incoming mail must be tied to an account without typing anything.

## Decision
Each user gets `u-<8 hex>@<domain>`; the webhook maps the recipient to the user.

## Consequences
Unguessable-ish alias; rotate/regenerate and rate-limit before production.
