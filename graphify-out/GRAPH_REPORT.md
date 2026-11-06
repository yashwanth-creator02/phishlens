# Graph Report - phishlens  (2026-11-05)

## Corpus Check
- 119 files · ~57,624 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 24 file(s) not represented in the graph (top: .mmd 9, (none) 5, .eml 4)

## Summary
- 686 nodes · 1361 edges · 55 communities (33 shown, 22 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 84 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e3b04528`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Email Feature Extraction
- Frontend React Client
- analysis_service.py
- Explainability and Reasoning Rules
- Sender Behavioral Profiling
- Document Formatting Utilities
- Analyses API Endpoints
- Model Training Pipeline
- Frontend Package Configuration
- Docker Compose Configuration
- GitHub Actions CI
- App Lifecycle and Dependencies
- TypeScript Configuration
- Report Chapter 4: Proposed Methodology (Part 1)
- models.py
- API Integration Tests
- SHAP Explanation Engine
- docs/README.md
- Pipeline Specifications and Tables
- Slide Deck Generation
- Matplotlib Figure Generation
- decisions/README.md
- webhooks.py
- test_reasons_and_bands.py
- Vite TypeScript Environment
- Container Entrypoint Script
- repository.py
- User Study Objectives
- 4 (continued). Proposed methodology - implementation view, then Expected outcomes and Conclusion
- report/README.md
- Database ERD Diagram
- Deployment Architecture Diagram
- Project Schedule Gantt Chart
- SHAP Explainability Diagram
- Slide Deck Documentation
- 02 - Project log: what was done, in order, and why
- 12 - Deployment
- 03 - Plan and roadmap
- Feature Extraction Engine
- 5. Expected outcomes
- Training report
- PhishLens Frontend Refinement and Defect Resolution Report
- 06-frontend-design.md
- 15 - Risks and limitations
- _sources/README.md

## God Nodes (most connected - your core abstractions)
1. `analyze()` - 30 edges
2. `ExtractionContext` - 26 edges
3. `parse_email()` - 25 edges
4. `ParsedEmail` - 18 edges
5. `Settings` - 17 edges
6. `ProfileData` - 17 edges
7. `ModelBundle` - 17 edges
8. `compilerOptions` - 17 edges
9. `update_profile()` - 15 edges
10. `build_samples()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `Scaling and the async path` --references--> `analyze()`  [INFERRED]
  docs/12-deployment.md → backend/app/services/analysis_service.py
- `11 - Security and privacy` --references--> `_own()`  [INFERRED]
  docs/11-security-privacy.md → backend/app/api/analyses.py
- `Task checklist` --references--> `DomainAgeProvider`  [INFERRED]
  docs/03-plan-and-roadmap.md → backend/app/features/common.py
- `Detailed Processing Pipeline Diagram` --references--> `Report Chapter 4: Proposed Methodology (Part 1)`  [EXTRACTED]
  docs/diagrams/fig2_pipeline.png → docs/report/03-proposed-methodology-part-1.md
- `End-to-End Sequence Diagram` --references--> `Report Chapter 4: Proposed Methodology (Part 1)`  [EXTRACTED]
  docs/diagrams/fig3_sequence.png → docs/report/03-proposed-methodology-part-1.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Literature to Methodology Specification Chain** — docs_report_01_introduction_and_literature_survey_doc, docs_report_02_problem_identification_and_objectives_doc, docs_report_03_proposed_methodology_part_1_doc [EXTRACTED 0.95]
- **PhishLens Core Detection and Explanation Pipeline** — docs_original_first_architecture_design_email_parser, docs_original_first_architecture_design_feature_extraction_engine, docs_original_first_architecture_design_shap_engine, docs_original_first_architecture_design_risk_scorer [EXTRACTED 0.95]
- **Core Architectural Decisions** — docs_decisions_adr_001_modular_monolith_adr001, docs_decisions_adr_002_inbound_email_webhook_first_gmail_api_later_adr002, docs_decisions_adr_003_shared_feature_code_for_training_and_serving_adr003, docs_decisions_adr_004_synchronous_processing_first_adr004 [EXTRACTED 1.00]
- **PhishLens Analysis and Triage Flow** — docs_04_architecture_email_parser, docs_04_architecture_feature_engine, docs_04_architecture_ml_inference, docs_04_architecture_shap_engine, docs_04_architecture_reason_engine, docs_04_architecture_risk_scorer [EXTRACTED 1.00]
- **Model Training and Synthetic Data Handling** — docs_decisions_adr_006_forwarding_prefer_attachment_adr_006, docs_decisions_adr_007_sender_history_only_from_safe_or_known_good_mail_adr_007, docs_decisions_adr_009_synthetic_generator_is_for_pipeline_testing_only_adr_009 [INFERRED 0.80]

## Communities (55 total, 22 thin omitted)

### Community 0 - "Email Feature Extraction"
Cohesion: 0.09
Nodes (27): extract(), _ext(), extract(), cosine_distance(), extract(), style_vector(), clip(), count_hits() (+19 more)

### Community 1 - "Frontend React Client"
Cohesion: 0.09
Nodes (35): dependencies, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, @supabase/supabase-js@^2.46.0, api, authHeaders(), request() (+27 more)

### Community 2 - "analysis_service.py"
Cohesion: 0.19
Nodes (11): Base, EmailRaw, Explanation, FeatureValue, band_for(), to_score(), add_baseline(), analyze() (+3 more)

### Community 4 - "Sender Behavioral Profiling"
Cohesion: 0.09
Nodes (35): update_profile(), DomainAgeProvider, NullDomainAge, ProfileData, extract_all(), FeatureResult, _inline_forward(), parse_email() (+27 more)

### Community 5 - "Document Formatting Utilities"
Cohesion: 0.08
Nodes (26): B(), BORDER, BORDERS, caption(), cellParas(), cite(), d, F() (+18 more)

### Community 6 - "Analyses API Endpoints"
Cohesion: 0.16
Nodes (21): delete_analysis(), _detail(), get_analysis(), get_features(), list_analyses(), model_info(), my_alias(), _own() (+13 more)

### Community 7 - "Model Training Pipeline"
Cohesion: 0.09
Nodes (11): clear_cache(), client(), make_client(), _make(), model_dir(), _reset_caches(), main(), make_models() (+3 more)

### Community 8 - "Frontend Package Configuration"
Cohesion: 0.12
Nodes (20): devDependencies, @types/react@^18.3.12, @types/react-dom@^18.3.1, typescript@^5.6.3, vite@^5.4.11, @vitejs/plugin-react@^4.3.4, name, private (+12 more)

### Community 9 - "Docker Compose Configuration"
Cohesion: 0.10
Nodes (20): VITE_SUPABASE_ANON_KEY, VITE_SUPABASE_URL, build, env_file, environment, ports, volumes, args (+12 more)

### Community 10 - "GitHub Actions CI"
Cohesion: 0.11
Nodes (20): defaults, runs-on, steps, run, defaults, runs-on, steps, jobs (+12 more)

### Community 11 - "App Lifecycle and Dependencies"
Cohesion: 0.14
Nodes (10): active_model(), current_user(), get_settings(), get_engine(), get_sessionmaker(), init_db(), health(), lifespan() (+2 more)

### Community 12 - "TypeScript Configuration"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 13 - "Report Chapter 4: Proposed Methodology (Part 1)"
Cohesion: 0.29
Nodes (7): Detailed Processing Pipeline Diagram, End-to-End Sequence Diagram, ML Workflow and Model Development Diagram, Methodology Phases and Output Diagram, Candidate ML Models (Logistic Regression, Random Forest, XGBoost), Report Chapter 4: Proposed Methodology (Part 1), Six Feature Groups Extraction

### Community 15 - "API Integration Tests"
Cohesion: 0.23
Nodes (9): token_for(), test_auth_required_and_users_are_isolated(), test_baseline_builds_history_and_high_risk_does_not_pollute_it(), test_inline_forward_is_analysed(), test_legitimate_mail_is_low(), test_list_detail_features_delete(), test_phishing_is_scored_high_with_verified_reasons(), test_webhook_requires_secret_and_known_alias() (+1 more)

### Community 16 - "SHAP Explanation Engine"
Cohesion: 0.36
Nodes (3): contributions(), _explainer(), ModelBundle

### Community 17 - "docs/README.md"
Cohesion: 0.20
Nodes (9): 11 - Security and privacy, Data handling summary, 13 - Testing and evaluation, Automated tests (`cd backend && python -m pytest -q`) - 28 passing, Evaluation experiments (to run on REAL data), What not to claim, PhishLens documentation index, 6. Conclusion (+1 more)

### Community 18 - "Pipeline Specifications and Tables"
Cohesion: 0.22
Nodes (9): Email Parser, ML Inference, Reason Engine, Risk Scorer, SHAP Explainer Engine, Analysis Service Pipeline, Analyses Table, Sender Profiles Table (+1 more)

### Community 19 - "Slide Deck Generation"
Cohesion: 0.36
Nodes (4): dup_para(), setc(), setp(), shape()

### Community 21 - "decisions/README.md"
Cohesion: 0.07
Nodes (31): PhishLens Project, Modular Monolith Architecture, Inbound Webhook Endpoint, ADR-001: Modular Monolith, ADR-002: Inbound Email Webhook First, ADR-003: Shared Feature Code for Training and Serving, ADR-004: Synchronous Processing First, ADR-005: Template-based explanations, no LLM in v1 (+23 more)

### Community 22 - "webhooks.py"
Cohesion: 0.16
Nodes (3): inbound(), Settings, get_db()

### Community 23 - "test_reasons_and_bands.py"
Cohesion: 0.28
Nodes (10): build_reasons(), fallback_reason(), Reason, _evidence(), test_behaviour_reason_suppressed_on_cold_start(), test_fallback_reason_is_generic_and_makes_no_specific_claim(), test_negative_contributions_never_become_reasons(), test_reason_with_evidence_uses_real_values() (+2 more)

### Community 26 - "repository.py"
Cohesion: 0.28
Nodes (8): ModelVersion, SenderProfile, UserAlias, get_or_create_alias(), load_profile(), save_profile(), sync_model_version(), user_for_alias_token()

### Community 35 - "4 (continued). Proposed methodology - implementation view, then Expected outcomes and Conclusion"
Cohesion: 0.15
Nodes (13): 4.10 Risk scoring and bands, 4.11 Backend and API design, 4.12 Data model, 4.13 Frontend, 4.14 Deployment and scalability, 4.15 Security and privacy, 4.16 Browser add-on (optional), 4.17 User evaluation (+5 more)

### Community 36 - "report/README.md"
Cohesion: 0.22
Nodes (8): 01 Project Overview, Feature Extraction Engine, 57 Features in Six Groups, Original PhishLens Project Definition, References (IEEE style), Report Chapter 1 & 2: Introduction and Literature Survey, Report Chapter 3: Problem Identification and Objectives, Project report (Markdown source)

### Community 45 - "02 - Project log: what was done, in order, and why"
Cohesion: 0.22
Nodes (9): 02 - Project log: what was done, in order, and why, 0. Starting point, 1. Architecture design  - DONE, 2. Visualisations  - DONE, 3. Literature survey, problem identification, methodology (project report content)  - PARTIAL, 4. Review-1 slide deck  - DONE, 5. Repository v0.1 (this zip)  - DONE (with stated limits), 6. Decisions awaiting the team (+1 more)

### Community 46 - "12 - Deployment"
Cohesion: 0.25
Nodes (7): 12 - Deployment, Docker Compose, Hosting options (provider not fixed), Inbound email, Local (no Docker), Scaling and the async path, Supabase

### Community 47 - "03 - Plan and roadmap"
Cohesion: 0.29
Nodes (7): 03 - Plan and roadmap, Definition of done (per increment), Immediate next steps (first two weeks), Increments, Indicative 16-week plan (matches report Fig. 8), Open decisions (need the team), Strategy

### Community 48 - "Feature Extraction Engine"
Cohesion: 0.40
Nodes (6): PhishLens System Architecture (v1 Design), Email Parser, Feature Extraction Engine, Risk Scorer, Sender History Store, SHAP Explainer Engine

### Community 49 - "5. Expected outcomes"
Cohesion: 0.33
Nodes (6): 5.1 Deliverables, 5.2 Planned measurable targets (to be validated, not results), 5.3 Expected contributions, 5.4 Impact (SDG 9: targets 9.1, 9.c, 9.5), 5.5 Anticipated limitations and future work, 5. Expected outcomes

### Community 50 - "Training report"
Cohesion: 0.40
Nodes (4): Ablation (XGBoost, drop one feature group), Held-out test set (uncalibrated models), Selected model after isotonic calibration (test), Training report

### Community 51 - "PhishLens Frontend Refinement and Defect Resolution Report"
Cohesion: 0.40
Nodes (4): Implemented Items, PhishLens Frontend Refinement and Defect Resolution Report, Summary of Work, Verification

### Community 52 - "06-frontend-design.md"
Cohesion: 0.50
Nodes (3): 06 - Frontend design, Next UI work, Screenshots (captured from the running app with the synthetic demo model)

### Community 53 - "15 - Risks and limitations"
Cohesion: 0.67
Nodes (3): 15 - Risks and limitations, Known limitations of v0.1 (honest list), Project risks

## Knowledge Gaps
- **28 isolated node(s):** `Risk Scorer`, `Sender History Store`, `Six Feature Groups Extraction`, `Detailed Processing Pipeline Diagram`, `End-to-End Sequence Diagram` (+23 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 299 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DomainAgeProvider` connect `Sender Behavioral Profiling` to `Email Feature Extraction`, `analysis_service.py`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `analyze()` (e.g. with `Settings` and `DomainAgeProvider`) actually correct?**
  _`analyze()` has 6 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Risk Scorer`, `Sender History Store`, `Six Feature Groups Extraction` to the rest of the system?**
  _28 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Email Feature Extraction` be split into smaller, more focused modules?**
  _Cohesion score 0.08755760368663594 - nodes in this community are weakly interconnected._
- **Why does `03 - Plan and roadmap` connect `03 - Plan and roadmap` to `docs/README.md`, `Sender Behavioral Profiling`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `ExtractionContext` (e.g. with `extract()` and `extract()`) actually correct?**
  _`ExtractionContext` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Should `Frontend React Client` be split into smaller, more focused modules?**
  _Cohesion score 0.09333333333333334 - nodes in this community are weakly interconnected._