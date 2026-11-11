# 04 - Architecture

PhishLens is a **modular monolith**: one deployable FastAPI service whose internal modules have clear boundaries, plus a
managed Supabase backend and a React frontend. Any module can later be moved into its own service without rewriting the others.

## Design principles
1. **One workflow, no forms** - the only user action is forwarding an email.
2. **Explainability is structural** - SHAP output drives the explanation text; reasons are verified against extracted evidence.
3. **Train/serve parity** - `backend/app/features/` is imported by both the API and `training/`; feature logic exists once (ADR-003).
4. **Synchronous first, async-ready** - a queue can later sit between "received" and "processed" (ADR-004).
5. **Safe by default** - attachments are never opened; history is never learned from risky mail; unsupported statements are never shown.
6. **Honest about uncertainty** - missing evidence is encoded as *missing*, not as *bad*; weak cases get a generic reason, not an invented one.

## System context
![System context](diagrams/fig1_context.png)

<details><summary>Mermaid source</summary>

```mermaid
flowchart TB
  U["User's email client<br/>(Gmail / Outlook)"]
  subgraph ING["Ingestion"]
    BOT["PhishLens bot address<br/>inbound webhook / Gmail API"]
  end
  subgraph BE["FastAPI backend (modular monolith)"]
    direction TB
    PARSE["Email parser"]
    FEAT["Feature extraction engine"]
    ML["ML inference"]
    SHAP["SHAP explainer"]
    EXP["Explanation generator"]
    RISK["Risk scorer"]
    API["REST API layer"]
  end
  subgraph SB["Supabase (managed)"]
    DB[("PostgreSQL")]
    AUTH["Supabase Auth"]
    STORE[("Storage: raw emails")]
  end
  FE["React + TypeScript web app"]
  U -->|forward| BOT
  BOT --> PARSE
  PARSE --> STORE
  PARSE --> FEAT
  FEAT <--> DB
  FEAT --> ML
  ML --> SHAP --> EXP --> API
  ML --> RISK --> API
  API <--> DB
  API <--> AUTH
  API <--> FE
  FE <--> AUTH
```
</details>

## Detailed processing pipeline
![Pipeline](diagrams/fig2_pipeline.png)

<details><summary>Mermaid source</summary>

```mermaid
flowchart TB
  A["Email client<br/>user forwards suspicious email"] --> B["Ingestion<br/>inbound webhook or bot inbox"]
  B --> C["Email parser<br/>headers, body, links, files"]
  subgraph FX["Feature extraction (six modules, one feature vector)"]
    direction LR
    F1["Header"] ~~~ F2["URL"] ~~~ F3["Text"] ~~~ F4["Action"] ~~~ F5["Attachment"] ~~~ F6["Behaviour"]
  end
  C --> FX
  FX --> M["ML inference<br/>LR / Random Forest / XGBoost"]
  M --> S["SHAP explainer<br/>per-prediction feature contributions"]
  M --> R["Risk scorer<br/>0-100 score, Low / Medium / High"]
  S --> E["Explanation generator<br/>feature to plain-language reason"]
  E --> API["API layer"]
  R --> API
  API --> DB[("Supabase<br/>database, auth, storage")]
  DB --> FE["React web interface<br/>score, band, reasons"]
```
</details>

## End-to-end sequence
![Sequence](diagrams/fig3_sequence.png)

<details><summary>Mermaid source</summary>

```mermaid
sequenceDiagram
    participant U as User
    participant EM as Email provider
    participant WH as Ingestion webhook
    participant BE as FastAPI backend
    participant DB as Supabase DB
    participant FE as Web frontend
    U->>EM: Forward suspicious email
    EM->>WH: Deliver to bot address
    WH->>BE: POST raw MIME (signed)
    BE->>BE: Parse headers, body, URLs, attachments
    BE->>DB: Fetch sender history
    BE->>BE: Extract feature vector
    BE->>BE: model.predict_proba(features)
    BE->>BE: SHAP explain(features, prediction)
    BE->>BE: Generate reasons + risk band
    BE->>DB: Store analysis, features, explanation
    BE->>DB: Update sender profile
    U->>FE: Open PhishLens dashboard
    FE->>BE: GET /api/analyses/{id}
    BE-->>FE: score, band, reasons
    FE-->>U: Rendered result
```
</details>

## Components and where they live in the repo

| Component | Responsibility | Code |
|---|---|---|
| Ingestion | receive forwarded mail (raw MIME or JSON), verify shared secret, map recipient alias -> user | `backend/app/api/webhooks.py` |
| Email parser | MIME -> headers, text, links (+anchor text), attachment metadata; detect forward-as-attachment / inline | `backend/app/ingestion/email_parser.py` |
| Feature engine | six modules -> 65 features + evidence | `backend/app/features/*.py` |
| Sender history | per (user, sender) rolling profile | `features/behavioral_features.py`, `db/repository.py` |
| Model registry | load `models/active/` (model, calibrator, background, meta) and check feature-set match | `backend/app/ml/registry.py` |
| SHAP engine | per-prediction contributions (Tree/Linear explainer) | `backend/app/explain/shap_engine.py` |
| Reason engine | 18 evidence-checked rules, selection rules, fallback | `explain/templates.py`, `explain/reasons.py` |
| Risk scorer | probability -> score -> band | `backend/app/scoring/risk_bands.py` |
| Pipeline | orchestrates everything and persists | `backend/app/services/analysis_service.py` |
| API | REST for the UI | `backend/app/api/analyses.py` |
| Database | SQLAlchemy models (SQLite / Postgres) | `backend/app/db/` , `supabase/migrations/0001_init.sql` |
| Web UI | dashboard, detail, settings, login | `frontend/src/` |

## Deployment view
![Deployment](diagrams/fig5_deploy.png)

## Forwarding behaviour (important)
* **Forward as attachment** -> original headers intact -> SPF/DKIM/DMARC usable.
* **Inline forward** -> the quoted header block is parsed for From/Reply-To/Subject/Date, but authentication results are
  unrecoverable -> features marked missing (`auth_missing = 1`).
* **Direct** (dev upload) -> analysed as the original.
