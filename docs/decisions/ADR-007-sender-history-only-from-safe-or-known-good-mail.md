# ADR-007: Sender history only from safe or known-good mail

**Status:** accepted (v0.1)

## Context
If the system learned from every analysed email, an attacker could make a spoofed sender look 'normal' by sending it repeatedly. Also the bot sees only forwarded mail.

## Decision
History is updated from explicit known-good uploads (`/api/baseline`) and from analyses scored LOW - never MEDIUM/HIGH. Minimum history (3) before behavioural features count.

## Consequences
Poisoning resistance. Limitation: history is sparse in real use; a mailbox connector (future) would help. Tested in test_api.
