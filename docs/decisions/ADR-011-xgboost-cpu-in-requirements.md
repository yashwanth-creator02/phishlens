# ADR-011: xgboost-cpu in requirements

**Status:** accepted (v0.1)

## Context
The default xgboost wheel pulls multi-hundred-MB CUDA libraries on Linux.

## Decision
Use `xgboost-cpu` (same import name).

## Consequences
Small installs/CI. Swap to `xgboost` if a GPU is wanted.
