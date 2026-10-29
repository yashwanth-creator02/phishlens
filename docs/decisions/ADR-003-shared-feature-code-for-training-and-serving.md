# ADR-003: Shared feature code for training and serving

**Status:** accepted (v0.1)

## Context
Train/serve skew silently degrades deployed classifiers.

## Decision
`backend/app/features/` is the only place features are computed; `training/` imports it. Models store their feature-name list; the registry refuses a mismatch.

## Consequences
Changing a feature requires retraining (by design). Tests cover the registry.
