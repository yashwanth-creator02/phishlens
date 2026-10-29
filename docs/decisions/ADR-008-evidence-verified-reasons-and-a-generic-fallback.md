# ADR-008: Evidence-verified reasons and a generic fallback

**Status:** accepted (v0.1)

## Context
A model attribution can point to a feature whose evidence is absent or misleading.

## Decision
Every rule has a `check` against extracted evidence; failing reasons are discarded. MEDIUM/HIGH with no verified reason shows one generic sentence.

## Consequences
No hallucinated statements. Some true model signals will not be shown if no rule covers them - extend rules from error analysis.
