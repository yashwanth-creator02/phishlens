# ADR-013: Calibrated probability and configurable bands

**Status:** accepted (v0.1)

## Context
The percentage shown should behave like a risk estimate; thresholds depend on data and tolerance for false alarms.

## Decision
Isotonic calibration on the validation split; score = round(100 p); band thresholds from settings; band stored with each analysis.

## Consequences
Thresholds (29/70) are provisional. Calibration shares the validation split with selection (optimistic) - fix for final results.
