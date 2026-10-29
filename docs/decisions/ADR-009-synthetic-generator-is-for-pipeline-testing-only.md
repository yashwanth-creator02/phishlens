# ADR-009: Synthetic generator is for pipeline testing only

**Status:** accepted (v0.1)

## Context
Real corpora take time; the system must be testable now.

## Decision
`training/synthetic.py` creates confusable legitimate mail, calm LLM-style phishing, spoofed known senders, forwarding wrappers and histories. Reports are stamped 'synthetic - not a result'; `/api/model` exposes `data_source` and the UI warns.

## Consequences
Lesson recorded: the first generator made 'no history' a perfect phishing cue (legitimate mail always had history), so the model flagged everything. Fixed (45% of legitimate mail is a first contact). Expect similar leaks with any generator - never report its numbers.
