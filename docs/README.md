# PhishLens documentation index

New here, or short on time? Read [**PhishLens in one page**](SUMMARY.md) first - the whole project in about three
minutes. The table below is the full set, for when you need the detail.

| # | Document | Read it for |
|---|---|---|
| 01 | [Project overview](01-project-overview.md) | the idea, user flow, scope, tech stack |
| 02 | [**Project log**](02-project-log.md) | **everything that was done so far, in order, and why** (research, design, report, slides, code) |
| 03 | [**Plan and roadmap**](03-plan-and-roadmap.md) | phases, week-by-week plan, task checklist, definition of done, next steps |
| 04 | [Architecture](04-architecture.md) | components, diagrams, data flow, design principles |
| 05 | [Backend design](05-backend-design.md) | modules, pipeline, config, how to extend |
| 06 | [Frontend design](06-frontend-design.md) | pages, API client, screenshots |
| 07 | [Data model](07-data-model.md) | tables, ERD, retention |
| 08 | [ML pipeline](08-ml-pipeline.md) | features (all 65), datasets, models, evaluation, behavioural benchmark |
| 09 | [Explainability](09-explainability.md) | SHAP, reason rules, verification, templates |
| 10 | [API reference](10-api-reference.md) | endpoints, payloads, webhook contract |
| 11 | [Security and privacy](11-security-privacy.md) | threats, mitigations, retention |
| 12 | [Deployment](12-deployment.md) | Docker, Supabase, hosting, async path |
| 13 | [Testing and evaluation](13-testing-and-evaluation.md) | test suite, evaluation experiments E1-E8 |
| 14 | [User study](14-user-study.md) | protocol to test whether explanations help |
| 15 | [Risks and limitations](15-risks-and-limitations.md) | what can go wrong, what is not done |
| 16 | [Demo script](16-demo-script.md) | what to click during the review, and what to say |
| 17 | [**Real-corpus evaluation**](17-real-corpus-evaluation.md) | **measured** numbers on Nazario + SpamAssassin, the grouped split, and what they do not prove |
| 18 | [**Open manual actions**](18-open-manual-actions.md) | **what still needs you**: Space creation, Supabase auth settings, with exact values |
| 19 | [**Teammate training guide**](19-teammate-training-guide.md) | exact commands to download the corpora, run evaluation, train and ship the real model |
| 20 | [**Model parameters and features**](20-model-parameters-and-features.md) | **the 65 features**, candidate hyperparameters, selection rule, calibration, bands, reason threshold |
| - | [File inventory](FILE_INVENTORY.md) | what each tracked path is for |
| - | [Dataset card](datasets/README.md) | corpus sources, licences, fetch command, split rules |
| - | [Decision log (ADRs)](decisions/) | why each important choice was made |
| - | [Final report](report/final-report.md) | submission write-up: objectives, what was built, verified results, limits |
| - | [Feature expansion report](report/2026-11-10-feature-expansion-report.md) | 57 to 65 features, retrained model, ablation read, malformed-port fix |
| - | [Project report (Markdown)](report/) | literature survey, problem, objectives, methodology (Word build still pending) |
| - | [References](references.md) | 37 IEEE-style references |
| - | [Review-1 slide deck](presentation/) | PhishLens_Review1.pptx + how it was derived |
| - | [Diagrams](diagrams/) | Mermaid sources + PNGs |
| - | [Original inputs](original/) | the first project definition, your synopsis, the evaluation rubric |
