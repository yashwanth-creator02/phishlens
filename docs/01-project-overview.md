# 01 - Project overview

## One sentence
Forward a suspicious email to a bot address and get a **Low / Medium / High** risk level plus **verified, plain-language
reasons**, instead of a bare "suspicious" verdict.

## Problem (from the synopsis)
Detectors give a classification but not reasons users can understand (P1); they rely on one kind of evidence and vary with
data (P2); and few systems test whether the explanations actually help users (P3). Generative AI makes fluent phishing cheap,
so grammar is no longer a reliable clue. Full argument with references: [report chapters 1-3](report/).

## Objectives (from the synopsis)
1. Build a multi-signal dataset/feature set across six clue categories and document each feature.
2. Evaluate an existing detection model and develop our own (LR, RF, XGBoost); compare with F1, ROC-AUC and error analysis; select one.
3. Integrate SHAP and convert contributions into clear user statements.
4. Evaluate the system, analyse errors, deliver results through a web interface fed by the email-forwarding workflow.
5. Evaluate whether explanations help users; as a stretch, a browser add-on.

Measurable success criteria (planned targets, to be validated): see [report/02](report/02-problem-identification-and-objectives.md) section 3.4.1.

## User flow
1. User gets a suspicious email. 2. Forwards it (preferably **as attachment**) to `u-<token>@<domain>` (their personal alias).
3. Inbound provider POSTs it to `/api/webhooks/inbound`. 4. Backend parses -> features -> model -> SHAP -> reasons -> stores.
5. User opens the web UI: score, band, reasons, evidence, history.

## The six evidence groups (57 features in v0.1)
Header/sender - URL - Language/tone - Requested action - Attachments - Sender behaviour. Full list: [08-ml-pipeline.md](08-ml-pipeline.md).

## Scope
In: English email; headers, text, links, requested actions, attachment *metadata*, sender history; Low/Medium/High + reasons;
web UI; forward-to-bot. Out: images/QR/voice, opening/executing attachments, auto-quarantine in the mailbox, non-email channels.

## Stack
React + TypeScript (Vite) - FastAPI (Python 3.12) - scikit-learn, XGBoost (CPU), SHAP - SQLAlchemy (SQLite locally, Supabase
PostgreSQL in production) - Supabase Auth (JWT) - Docker. LLMs are **not** in the core path (ADR-005).

## SDG
SDG 9 (Industry, Innovation and Infrastructure): targets 9.1, 9.c, 9.5.
