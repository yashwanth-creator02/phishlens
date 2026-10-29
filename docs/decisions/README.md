# Decision log (Architecture Decision Records)

Each ADR: context -> decision -> consequences. Status: accepted for v0.1 unless noted.

| ADR | Title |
|---|---|
| [001](ADR-001-modular-monolith.md) | Modular monolith (one FastAPI service) |
| [002](ADR-002-inbound-email-webhook-first-gmail-api-later.md) | Inbound email webhook first, Gmail API later |
| [003](ADR-003-shared-feature-code-for-training-and-serving.md) | Shared feature code for training and serving |
| [004](ADR-004-synchronous-processing-first.md) | Synchronous processing first |
| [005](ADR-005-template-based-explanations-no-llm-in-v1.md) | Template-based explanations, no LLM in v1 |
| [006](ADR-006-forwarding-prefer-attachment.md) | Forwarding: prefer attachment; treat inline authentication as missing |
| [007](ADR-007-sender-history-only-from-safe-or-known-good-mail.md) | Sender history only from safe or known-good mail |
| [008](ADR-008-evidence-verified-reasons-and-a-generic-fallback.md) | Evidence-verified reasons and a generic fallback |
| [009](ADR-009-synthetic-generator-is-for-pipeline-testing-only.md) | Synthetic generator is for pipeline testing only |
| [010](ADR-010-sqlalchemy-with-sqlite-for-development-and-postgresql.md) | SQLAlchemy with SQLite for development and PostgreSQL (Supabase) for production |
| [011](ADR-011-xgboost-cpu-in-requirements.md) | xgboost-cpu in requirements |
| [012](ADR-012-per-user-forwarding-alias.md) | Per-user forwarding alias |
| [013](ADR-013-calibrated-probability-and-configurable-bands.md) | Calibrated probability and configurable bands |
| [014](ADR-014-never-open-or-execute-attachments.md) | Never open or execute attachments |
