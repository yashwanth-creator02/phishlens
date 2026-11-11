# Graph Report - phishlens  (2026-11-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1052 nodes · 2087 edges · 67 communities (46 shown, 21 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 133 edges (avg confidence: 0.93)
- Token cost: 2,236 input · 548 output

## Graph Freshness
- Built from commit: `2cf6fbdd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Email Feature Extraction
- Data Repository and Profiles
- Frontend Testing and Tooling
- Explainability and Reasoning Rules
- Sender Behavioral Profiling
- Document Formatting Utilities
- Analyses API Endpoints
- Domain and Corpus Processing
- Frontend Auth and API
- Database Models and Session
- GitHub Actions CI
- App Lifecycle and Dependencies
- TypeScript Configuration
- CI/CD Workflows
- Setup and Installation Guide
- API Integration Tests
- Project Scope and Design
- Model Analysis and SHAP
- Security and RLS Testing
- Deployment Configuration
- Model Parameters and Features
- Project Documentation and Planning
- Application Settings and Webhooks
- Project Report Structure
- Vite TypeScript Environment
- Container Entrypoint Script
- API Auth and Scoring
- Model Evaluation Results
- Explainability Module Package
- Ingestion Module Package
- Project File Inventory
- Project Overview and Summary
- Feature Expansion Report
- Test Suite Package
- Database URL Utilities
- Presentation Deck Automation
- Demo Script and Flow
- Manual Deployment Actions
- Deployment Architecture Diagram
- Project Schedule Gantt Chart
- SHAP Explainability Diagram
- Slide Deck Documentation
- Report Chapter One Scripts
- Report Chapter Three Scripts
- Testing and Evaluation Strategy
- Risks and Limitations
- Vite Environment Types
- Docker Entrypoint Script
- Report Generator Source
- User Study Objectives
- Database ER Diagram
- Deployment Architecture Diagram
- Project Gantt Chart
- Explainability Architecture Diagram
- Slide Deck Documentation

## God Nodes (most connected - your core abstractions)
1. `analyze()` - 32 edges
2. `ExtractionContext` - 27 edges
3. `parse_email()` - 27 edges
4. `Settings` - 26 edges
5. `ProfileData` - 19 edges
6. `ParsedEmail` - 18 edges
7. `sample()` - 18 edges
8. `ModelBundle` - 17 edges
9. `Analysis` - 17 edges
10. `build_samples()` - 17 edges

## Surprising Connections (you probably didn't know these)
- `Scaling and the async path` --references--> `analyze()`  [INFERRED]
  docs/12-deployment.md → backend/app/services/analysis_service.py
- `If something goes wrong` --references--> `health()`  [INFERRED]
  docs/19-teammate-training-guide.md → backend/app/main.py
- `2026-11-06 (later) - Real-corpus download, loader fix, and the first measured result` --references--> `load_dir()`  [INFERRED]
  docs/02-project-log.md → backend/training/corpus.py
- `Step 4 - Download the real corpora` --references--> `load_dir()`  [INFERRED]
  docs/19-teammate-training-guide.md → backend/training/corpus.py
- `2026-11-06 (deployment) - Branches merged, frontend live on Vercel, Supabase provisioned` --references--> `init_db()`  [INFERRED]
  docs/02-project-log.md → backend/app/db/session.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Literature to Methodology Specification Chain** — docs_report_01_introduction_and_literature_survey_doc, docs_report_02_problem_identification_and_objectives_doc, docs_report_03_proposed_methodology_part_1_doc [EXTRACTED 0.95]
- **PhishLens Core Detection and Explanation Pipeline** — docs_original_first_architecture_design_email_parser, docs_original_first_architecture_design_feature_extraction_engine, docs_original_first_architecture_design_shap_engine, docs_original_first_architecture_design_risk_scorer [EXTRACTED 0.95]
- **Core Architectural Decisions** — docs_decisions_adr_001_modular_monolith_adr001, docs_decisions_adr_002_inbound_email_webhook_first_gmail_api_later_adr002, docs_decisions_adr_003_shared_feature_code_for_training_and_serving_adr003, docs_decisions_adr_004_synchronous_processing_first_adr004 [EXTRACTED 1.00]
- **PhishLens Analysis and Triage Flow** — docs_04_architecture_email_parser, docs_04_architecture_feature_engine, docs_04_architecture_ml_inference, docs_04_architecture_shap_engine, docs_04_architecture_reason_engine, docs_04_architecture_risk_scorer [EXTRACTED 1.00]
- **Model Training and Synthetic Data Handling** — docs_decisions_adr_006_forwarding_prefer_attachment_adr_006, docs_decisions_adr_007_sender_history_only_from_safe_or_known_good_mail_adr_007, docs_decisions_adr_009_synthetic_generator_is_for_pipeline_testing_only_adr_009 [INFERRED 0.80]

## Communities (67 total, 21 thin omitted)

### Community 0 - "Email Feature Extraction"
Cohesion: 0.06
Nodes (48): extract(), _ext(), extract(), cosine_distance(), extract(), style_vector(), update_profile(), clip() (+40 more)

### Community 1 - "Data Repository and Profiles"
Cohesion: 0.11
Nodes (16): ModelVersion, SenderProfile, UserAlias, delete_analysis(), get_or_create_alias(), load_profile(), load_sender_profile(), purge_expired() (+8 more)

### Community 2 - "Frontend Testing and Tooling"
Cohesion: 0.07
Nodes (34): devDependencies, jsdom@^31.0.0, @playwright/test@^1.65.0, @testing-library/jest-dom@^7.0.1, @testing-library/react@^16.3.3, @testing-library/user-event@^14.6.8, @types/react@^18.3.12, @types/react-dom@^18.3.1 (+26 more)

### Community 3 - "Explainability and Reasoning Rules"
Cohesion: 0.07
Nodes (11): build_reasons(), fallback_reason(), Reason, Rule, _evidence(), test_behaviour_reason_suppressed_on_cold_start(), test_fallback_reason_is_generic_and_makes_no_specific_claim(), test_negative_contributions_never_become_reasons() (+3 more)

### Community 4 - "Sender Behavioral Profiling"
Cohesion: 0.08
Nodes (26): B(), BORDER, BORDERS, caption(), cellParas(), cite(), d, F() (+18 more)

### Community 5 - "Document Formatting Utilities"
Cohesion: 0.07
Nodes (31): PhishLens Project, Modular Monolith Architecture, Inbound Webhook Endpoint, ADR-001: Modular Monolith, ADR-002: Inbound Email Webhook First, ADR-003: Shared Feature Code for Training and Serving, ADR-004: Synchronous Processing First, ADR-005: Template-based explanations, no LLM in v1 (+23 more)

### Community 6 - "Analyses API Endpoints"
Cohesion: 0.15
Nodes (22): delete_analysis(), _detail(), get_analysis(), get_features(), list_analyses(), model_info(), my_alias(), _own() (+14 more)

### Community 7 - "Domain and Corpus Processing"
Cohesion: 0.07
Nodes (34): DomainAgeProvider, NullDomainAge, split_host(), test_load_dir_accepts_extensionless_hash_named_files(), test_load_dir_reads_mbox_next_to_loose_files(), test_load_mailbox_filters_spam_and_trash(), _iter_raw(), load_dir() (+26 more)

### Community 8 - "Frontend Auth and API"
Cohesion: 0.05
Nodes (66): 10. Auth, deployment, and frontend foundation, `frontend/`, Self-Review, Task 10: Settings, login, and status, Task 6: Frontend API and auth foundation, dependencies, react@^18.3.1, react-dom@^18.3.1 (+58 more)

### Community 9 - "Database Models and Session"
Cohesion: 0.18
Nodes (16): Analysis, Base, EmailRaw, Explanation, FeatureValue, get_db(), get_engine(), get_sessionmaker() (+8 more)

### Community 10 - "GitHub Actions CI"
Cohesion: 0.08
Nodes (27): Global Constraints, PhishLens Mini-Project Delivery Plan, Review Focus, Task 11: Vercel frontend deployment, Task 12: End-to-end smoke and submission docs, Task 1: Supabase schema and RLS verification, Task 2: Real-data evaluation pipeline, Task 3: Supabase auth and Postgres serving (+19 more)

### Community 11 - "App Lifecycle and Dependencies"
Cohesion: 0.15
Nodes (6): active_model(), get_settings(), health(), lifespan(), load_active(), ModelNotAvailable

### Community 12 - "TypeScript Configuration"
Cohesion: 0.10
Nodes (20): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, build, env_file, environment, ports, volumes, args (+12 more)

### Community 13 - "CI/CD Workflows"
Cohesion: 0.11
Nodes (20): defaults, runs-on, steps, run, defaults, runs-on, steps, jobs (+12 more)

### Community 14 - "Setup and Installation Guide"
Cohesion: 0.11
Nodes (19): Expected output, Expected output, Further reading, If something goes wrong, Known artefact - read before you are surprised, Prerequisites, Rules you must not break, Step 1 - Clone the repository (+11 more)

### Community 15 - "API Integration Tests"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 16 - "Project Scope and Design"
Cohesion: 0.11
Nodes (17): Approaches considered, Architecture, Builder-check resolutions, Constraints, Data, Frontend surface, Gmail path (stretch), Goals (+9 more)

### Community 17 - "Model Analysis and SHAP"
Cohesion: 0.18
Nodes (10): new_id(), contributions(), _explainer(), ModelBundle, band_for(), to_score(), analyze(), BaselineResult (+2 more)

### Community 18 - "Security and RLS Testing"
Cohesion: 0.05
Nodes (30): main(), test_wildcard_origin_is_rejected(), _tar_bz2(), test_multi_source_download_writes_manifest(), test_evaluation_no_cwd_reports(), test_evaluation_rejects_missing_corpora(), test_evaluation_uses_grouped_split(), _write_fixtures() (+22 more)

### Community 19 - "Deployment Configuration"
Cohesion: 0.14
Nodes (13): generateValue, key, sync, value, services, dockerContext, dockerfilePath, envVars (+5 more)

### Community 20 - "Model Parameters and Features"
Cohesion: 0.15
Nodes (13): 1. Model selection and training parameters, 2. Scoring and decision parameters, 3. Feature vector (65, in model order), 4. What the new v0.2 features do and do not buy, 5. Related pages, Action - 6, Attachment - 8, Behaviour - 10 (+5 more)

### Community 21 - "Project Documentation and Planning"
Cohesion: 0.20
Nodes (6): 11 - Security and privacy, Data handling summary, Database isolation verification, PhishLens documentation index, 6. Conclusion, PhishLens Overview

### Community 22 - "Application Settings and Webhooks"
Cohesion: 0.14
Nodes (3): current_user(), inbound(), Settings

### Community 23 - "Project Report Structure"
Cohesion: 0.15
Nodes (13): 10. Reading path, 1. Abstract, 2. Problem and objectives, 3.1 Pipeline, 3.2 Interfaces, 3. What was built, 4. Verification (what is actually tested), 5. Data and evaluation status (+5 more)

### Community 24 - "Vite TypeScript Environment"
Cohesion: 0.18
Nodes (11): Detailed Processing Pipeline Diagram, End-to-End Sequence Diagram, ML Workflow and Model Development Diagram, Methodology Phases and Output Diagram, References (IEEE style), Report Chapter 1 & 2: Introduction and Literature Survey, Report Chapter 3: Problem Identification and Objectives, Candidate ML Models (Logistic Regression, Random Forest, XGBoost) (+3 more)

### Community 25 - "Container Entrypoint Script"
Cohesion: 0.15
Nodes (13): 4.10 Risk scoring and bands, 4.11 Backend and API design, 4.12 Data model, 4.13 Frontend, 4.14 Deployment and scalability, 4.15 Security and privacy, 4.16 Browser add-on (optional), 4.17 User evaluation (+5 more)

### Community 26 - "API Auth and Scoring"
Cohesion: 0.14
Nodes (17): verify_supabase_token(), token_for(), test_auth_required_and_users_are_isolated(), test_baseline_builds_history_and_high_risk_does_not_pollute_it(), test_inline_forward_is_analysed(), test_legitimate_mail_is_low(), test_list_detail_features_delete(), test_phishing_is_scored_high_with_verified_reasons() (+9 more)

### Community 27 - "Model Evaluation Results"
Cohesion: 0.17
Nodes (12): Artefacts, Corpus, Known gaps, Model under evaluation, Per-group ablation (65 features, XGBoost), Promoted serving model (measured the same way), Real-Corpus Evaluation (measured), Reproducing (+4 more)

### Community 28 - "Explainability Module Package"
Cohesion: 0.17
Nodes (12): 01 Project Overview, Email Parser, Feature Extraction Engine, ML Inference, Reason Engine, Risk Scorer, SHAP Explainer Engine, Analysis Service Pipeline (+4 more)

### Community 29 - "Ingestion Module Package"
Cohesion: 0.27
Nodes (6): clear_cache(), client(), make_client(), _make(), model_dir(), _reset_caches()

### Community 30 - "Project File Inventory"
Cohesion: 0.20
Nodes (9): `backend/app/` - FastAPI service, `backend/data/sample_emails/`, `backend/tests/`, `backend/training/` and `backend/scripts/`, `docs/`, File inventory, Other, Repository root (+1 more)

### Community 31 - "Project Overview and Summary"
Cohesion: 0.20
Nodes (10): How it decides, in one line per step, PhishLens in one page, Run it locally (Windows), The idea, The live demo is a pipeline demo, not the model above, The numbers, with their caveats, What a user does, What is built (+2 more)

### Community 32 - "Feature Expansion Report"
Cohesion: 0.29
Nodes (6): Decisions, Documentation, Feature expansion, retrained model, and parameter documentation, Follow-ups, Retrained model, Verification

### Community 33 - "Test Suite Package"
Cohesion: 0.12
Nodes (16): 02 - Project log: what was done, in order, and why, 0. Starting point, 11. CORS hardening, browser smoke test, and submission docs, 1. Architecture design  - DONE, 2026-11-06 (deployment) - Branches merged, frontend live on Vercel, Supabase provisioned, 2026-11-06 (later) - Real-corpus download, loader fix, and the first measured result, 2026-11-10 - Feature expansion, retrained model, and parameter documentation, 2026-11-10 - Full Nazario corpus fetch and a one-page project summary (+8 more)

### Community 34 - "Database URL Utilities"
Cohesion: 0.60
Nodes (5): _normalize_url(), test_a_raw_at_sign_in_the_password_is_encoded(), test_an_already_encoded_password_is_not_double_encoded(), test_other_urls_are_left_alone(), test_postgres_urls_select_the_psycopg_driver()

### Community 35 - "Presentation Deck Automation"
Cohesion: 0.36
Nodes (4): dup_para(), setc(), setp(), shape()

### Community 36 - "Demo Script and Flow"
Cohesion: 0.33
Nodes (6): 16 - Demo script, Before the session (do the day before, not in the room), Closing (30 seconds), Demo flow, Fallbacks, Questions to expect

### Community 37 - "Manual Deployment Actions"
Cohesion: 0.33
Nodes (5): 1. Optional: send the demo through the real model (15 minutes, on your machine), 2. Optional: restore push-to-deploy for the backend (2 minutes), 3. Fallback if Render ever refuses you, Already handled - do not redo, Open manual actions

### Community 38 - "Deployment Architecture Diagram"
Cohesion: 0.18
Nodes (11): 12 - Deployment, Current frontend deployment, Current Supabase project, Docker Compose, Hosting options (provider not fixed), Inbound email, Local (no Docker), Render (free backend) (+3 more)

### Community 39 - "Project Schedule Gantt Chart"
Cohesion: 0.33
Nodes (7): PhishLens System Architecture (v1 Design), Email Parser, Feature Extraction Engine, Risk Scorer, Sender History Store, SHAP Explainer Engine, Original PhishLens Project Definition

### Community 40 - "SHAP Explainability Diagram"
Cohesion: 0.18
Nodes (9): 06 - Frontend design, Next UI work, Screenshots (captured from the running app with the synthetic demo model), 5.1 Deliverables, 5.2 Planned measurable targets (to be validated, not results), 5.3 Expected contributions, 5.4 Impact (SDG 9: targets 9.1, 9.c, 9.5), 5.5 Anticipated limitations and future work (+1 more)

### Community 41 - "Slide Deck Documentation"
Cohesion: 0.33
Nodes (5): buildCommand, framework, outputDirectory, rewrites, $schema

### Community 42 - "Report Chapter One Scripts"
Cohesion: 0.40
Nodes (4): Ablation (XGBoost, drop one feature group), Held-out test set (uncalibrated models), Selected model after isotonic calibration (test), Training report

### Community 43 - "Report Chapter Three Scripts"
Cohesion: 0.40
Nodes (4): Implemented Items, PhishLens Frontend Refinement and Defect Resolution Report, Summary of Work, Verification

### Community 44 - "Testing and Evaluation Strategy"
Cohesion: 0.33
Nodes (6): 13 - Testing and evaluation, Automated tests (`cd backend && python -m pytest -q`) - 52 passing, 1 skipped, Evaluation experiments (to run on REAL data), Frontend, Real-data evaluation harness, What not to claim

### Community 46 - "Risks and Limitations"
Cohesion: 0.67
Nodes (3): 15 - Risks and limitations, Known limitations of v0.1 (honest list), Project risks

## Knowledge Gaps
- **28 isolated node(s):** `Six Feature Groups Extraction`, `Detailed Processing Pipeline Diagram`, `End-to-End Sequence Diagram`, `ML Workflow and Model Development Diagram`, `Methodology Phases and Output Diagram` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 476 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `02 - Project log: what was done, in order, and why` connect `Test Suite Package` to `Frontend Auth and API`, `Project Documentation and Planning`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `analyze()` (e.g. with `Settings` and `DomainAgeProvider`) actually correct?**
  _`analyze()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Six Feature Groups Extraction`, `Detailed Processing Pipeline Diagram`, `End-to-End Sequence Diagram` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Email Feature Extraction` be split into smaller, more focused modules?**
  _Cohesion score 0.06235069278547539 - nodes in this community are weakly interconnected._
- **Why does `10. Auth, deployment, and frontend foundation` connect `Frontend Auth and API` to `Test Suite Package`?**
  _High betweenness centrality (0.160) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ExtractionContext` (e.g. with `extract()` and `extract()`) actually correct?**
  _`ExtractionContext` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Data Repository and Profiles` be split into smaller, more focused modules?**
  _Cohesion score 0.11491935483870967 - nodes in this community are weakly interconnected._