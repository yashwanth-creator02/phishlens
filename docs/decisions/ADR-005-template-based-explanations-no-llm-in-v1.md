# ADR-005: Template-based explanations, no LLM in v1

**Status:** accepted (v0.1)

## Context
Explanations must be faithful and cheap; literature warns LLM text can hallucinate features (Cau et al. 2025).

## Decision
SHAP -> rule engine -> templates filled from extracted evidence. LLM rewording of verified facts and counterfactuals are optional later extensions, still verification-gated.

## Consequences
Fully traceable sentences, no API cost. Less fluent than LLM text; wording quality needs a review round.
