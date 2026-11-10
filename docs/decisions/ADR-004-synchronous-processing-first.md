# ADR-004: Synchronous processing first

**Status:** accepted (v0.1)

## Context
Typical analysis is fast (parse + 65 features + one tree model + one SHAP pass).

## Decision
Process in the request/webhook. Reserve the queue seam (Redis + Celery) for when p95 latency requires it.

## Consequences
No extra infrastructure now. Webhook providers have timeouts - monitor; async path documented in 12-deployment.md.
