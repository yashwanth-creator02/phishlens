"""Task 4: retention, delete cascade, cold-start neutral senders.

The brief's `sender_history_count` feature name does not exist in the 65-feature
vector (feature names are fixed by training/serving parity). This module tests
the equivalent cold-start neutrality via the existing `prior_message_count`
feature and `insufficient_history`.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from app.core.config import Settings
from app.db import repository as repo
from app.db.models import Analysis, EmailRaw, Explanation, FeatureValue
from app.db.session import get_sessionmaker, init_db
from app.ml.registry import load_active
from app.services import analysis_service

from .conftest import sample

USER_ID = "retention-user"


def _settings(tmp_path, model_dir) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        storage_dir=tmp_path / "storage",
        model_dir=model_dir,
        retention_days=30,
        admin_token="test-admin-token",
    )


def _save_case(db, settings, bundle) -> Analysis:
    return analysis_service.analyze(db, settings, bundle, USER_ID, sample("phish_paypal_direct.eml"))


def test_delete_removes_children_and_file(tmp_path, model_dir):
    settings = _settings(tmp_path, model_dir)
    init_db()
    bundle = load_active(settings.model_dir)
    with get_sessionmaker()() as db:
        saved_case = _save_case(db, settings, bundle)
        case_id = saved_case.id
        storage_path = saved_case.raw.storage_path
        assert (tmp_path / "storage" / USER_ID / f"{case_id}.eml").exists()

        assert analysis_service.delete_analysis(db, USER_ID, case_id) is True
        assert db.get(Analysis, case_id) is None
        assert not (tmp_path / "storage" / USER_ID / f"{case_id}.eml").exists()
        assert not db.scalars(select(EmailRaw).where(EmailRaw.analysis_id == case_id)).first()
        assert not db.scalars(select(FeatureValue).where(FeatureValue.analysis_id == case_id)).first()
        assert not db.scalars(select(Explanation).where(Explanation.analysis_id == case_id)).first()


def test_delete_other_user_case_fails_and_file_survives(tmp_path, model_dir):
    settings = _settings(tmp_path, model_dir)
    init_db()
    bundle = load_active(settings.model_dir)
    with get_sessionmaker()() as db:
        saved_case = _save_case(db, settings, bundle)
        case_id = saved_case.id
        assert analysis_service.delete_analysis(db, "another-user", case_id) is False
        assert db.get(Analysis, case_id) is not None
        assert (tmp_path / "storage" / USER_ID / f"{case_id}.eml").exists()


def test_purge_expired_removes_old_across_users_and_files(tmp_path, model_dir):
    settings = _settings(tmp_path, model_dir)
    init_db()
    bundle = load_active(settings.model_dir)
    with get_sessionmaker()() as db:
        old = _save_case(db, settings, bundle)
        old.created_at = datetime.utcnow() - timedelta(days=90)
        other = analysis_service.analyze(
            db, settings, bundle, "other-user", sample("legit_newsletter.eml"))
        other.created_at = datetime.utcnow() - timedelta(days=90)
        new = _save_case(db, settings, bundle)
        db.commit()

        deleted = analysis_service.purge_expired(db, datetime.utcnow() - timedelta(days=30))
        assert deleted == 2
        assert db.get(Analysis, old.id) is None
        assert db.get(Analysis, other.id) is None
        assert db.get(Analysis, new.id) is not None
        assert not (tmp_path / "storage" / USER_ID / f"{old.id}.eml").exists()
        assert not (tmp_path / "storage" / "other-user" / f"{other.id}.eml").exists()


def test_first_time_sender_is_neutral(tmp_path, model_dir):
    settings = _settings(tmp_path, model_dir)
    init_db()
    with get_sessionmaker()() as db:
        profile = repo.load_sender_profile(db, USER_ID, "new@example.com")
        assert profile.message_count == 0
        assert profile.first_seen is None
        assert profile.last_seen is None

        features = analysis_service.build_features(db, settings, USER_ID, sample("phish_paypal_direct.eml"))
        # Existing neutral defaults: no prior history for a cold-start sender.
        assert features["prior_message_count"] == 0
        assert features["insufficient_history"] == 1
        assert features["sender_seen_before"] == 0
