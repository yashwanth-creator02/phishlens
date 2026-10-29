# ADR-006: Forwarding: prefer attachment; treat inline authentication as missing

**Status:** accepted (v0.1)

## Context
Inline forwards are re-sent by the forwarder, so the original SPF/DKIM/DMARC results are gone; forward-as-attachment keeps them.

## Decision
Parser handles both. Inline: recover quoted From/Reply-To/Subject/Date; authentication features = missing (not fail). UI advises "Forward as attachment".

## Consequences
Avoids false 'failed authentication' alarms. Trained models must see both forms (the generator wraps messages 40/30/30 direct/attachment/inline).
