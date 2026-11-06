# 05 - Backend design

Python 3.12, FastAPI, SQLAlchemy 2, scikit-learn, XGBoost (CPU), SHAP. Source: `backend/`.

## Layout
```
backend/
  app/
    main.py                 FastAPI app, lifespan (create tables, sync active model row), CORS, /api/health
    core/config.py          Settings (PHISHLENS_* env vars)
    api/                    deps.py (auth, active model) - analyses.py - webhooks.py
    ingestion/email_parser.py   MIME + forwarded-message handling
    features/               lexicons, common, header_, url_, text_, action_, attachment_, behavioral_, feature_vector
    ml/registry.py          load models/active/, feature-set guard, calibration
    explain/                shap_engine.py, templates.py (rules), reasons.py (selection + fallback)
    scoring/risk_bands.py   score + band + guidance
    db/                     models.py, session.py, repository.py
    services/analysis_service.py   the pipeline
    schemas.py              Pydantic response models
  training/                 synthetic.py, corpus.py, train.py
  tests/                    parser, features, reasons/bands, API (28 tests)
  data/sample_emails/       4 hand-written .eml samples
```

## The pipeline (`services/analysis_service.analyze`)
1. `parse_email(raw)` -> `ParsedEmail` (scope: direct / forward_attachment / forward_inline).
2. Load the sender's `ProfileData` for (user, sender) or `None`.
3. `extract_all(parsed, ctx)` -> 57 values + per-group *evidence* (the concrete things found: mismatching domains, phrases, file names...).
4. `bundle.predict(vector)` -> raw probability -> isotonic calibration -> `p_cal`.
5. `score = round(100 p_cal)`; `band_for(score)`.
6. `shap_engine.contributions` -> per-feature contributions to the phishing class.
7. `build_reasons` -> verified reasons (<= `top_k_reasons`); if band != LOW and none verified -> generic fallback.
8. Persist: analysis, raw file (`storage_dir/<user>/<id>.eml`), 57 feature rows (+ SHAP value), explanations.
9. If band == LOW -> update the sender profile (never for MEDIUM/HIGH).

## Configuration (env, prefix `PHISHLENS_`)
`DATABASE_URL`, `STORAGE_DIR`, `MODEL_DIR`, `AUTH_MODE` (`disabled`|`supabase`), `SUPABASE_JWT_SECRET`, `WEBHOOK_SECRET`, `ALIAS_DOMAIN`, `ADMIN_TOKEN`, `RETENTION_DAYS`
`CORS_ORIGINS`, `BAND_LOW_MAX`, `BAND_HIGH_MIN`, `TOP_K_REASONS`, `MIN_REASON_CONTRIBUTION`, `MIN_HISTORY_MESSAGES`, `RETENTION_DAYS`. See `.env.example`.

## Extension points
| To add... | Do this |
|---|---|
| a feature | add the name to the module's `NAMES`, compute it in `extract`, add evidence if it should become a reason; **retrain** (the registry refuses a model with a different feature list); add a test |
| a reason | add a `Rule` in `explain/templates.py` with a `check` that returns format values **only if evidence supports the claim**; add a test in `tests/test_reasons_and_bands.py` |
| domain age lookups | implement `DomainAgeProvider.age_days(registered_domain)` (RDAP/WHOIS, cache, short timeout) and pass it to `analyze(..., domain_age=...)`; train with it available for a share of samples |
| an email provider | write an adapter that turns the provider payload into raw MIME + recipient and call the same service (see webhook) |
| async processing | make the webhook enqueue a job (Redis + Celery) and return 202; run `analyze` in the worker; poll or use Supabase Realtime (no change to features/model/explain) |
| another model | add it to `make_models` in `training/train.py`; SHAP engine handles tree models and linear models |

## Failure behaviour
* No model -> API starts, `/api/health` says `degraded`, analysis endpoints return 503 with instructions.
* Model/feature mismatch -> 503 "retrain".
* Unparseable mail -> parser is defensive (undecodable parts skipped); empty/oversized upload -> 400/413.
* Unknown webhook alias -> 404; bad secret -> 401.
