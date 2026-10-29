# ADR-014: Never open or execute attachments

**Status:** accepted (v0.1)

## Context
Opening attachments is the riskiest operation a phishing analyser can perform.

## Decision
Only metadata (name, declared type, size, SHA-256) is extracted.

## Consequences
Cannot detect malicious content inside files; rely on type/name/MIME mismatch signals.
