from __future__ import annotations

from app.db.session import _normalize_url


def test_postgres_urls_select_the_psycopg_driver():
    # Supabase's Connect panel copies a bare postgresql:// string; psycopg2 is not installed.
    assert _normalize_url("postgresql://u:p@h:6543/postgres") == "postgresql+psycopg://u:p@h:6543/postgres"
    assert _normalize_url("postgres://u:p@h:5432/postgres") == "postgresql+psycopg://u:p@h:5432/postgres"


def test_other_urls_are_left_alone():
    assert _normalize_url("postgresql+psycopg://u:p@h/postgres") == "postgresql+psycopg://u:p@h/postgres"
    assert _normalize_url("sqlite:///./phishlens.db") == "sqlite:///./phishlens.db"
