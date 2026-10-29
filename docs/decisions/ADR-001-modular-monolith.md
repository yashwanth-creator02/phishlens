# ADR-001: Modular monolith (one FastAPI service)

**Status:** accepted (v0.1)

## Context
A four-student team needs something runnable, debuggable and deployable quickly; the pipeline stages share data structures.

## Decision
One service with internal modules (ingestion, features, ml, explain, scoring, db, services). Frontend and Supabase are separate. No microservices in v1.

## Consequences
Simple ops and tests. Seams exist to split ML inference or ingestion later. Risk: tight coupling creeping in - keep imports one-directional (api -> services -> features/ml/explain/db).
