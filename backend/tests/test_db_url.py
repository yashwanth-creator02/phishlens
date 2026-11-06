from __future__ import annotations

from app.db.session import _normalize_url


def test_postgres_urls_select_the_psycopg_driver():
    # Supabase's Connect panel copies a bare postgresql:// string; psycopg2 is not installed.
    assert _normalize_url("postgresql://u:p@h:6543/postgres") == "postgresql+psycopg://u:p@h:6543/postgres"
    assert _normalize_url("postgres://u:p@h:5432/postgres") == "postgresql+psycopg://u:p@h:5432/postgres"


def test_other_urls_are_left_alone():
    assert _normalize_url("postgresql+psycopg://u:p@h/postgres") == "postgresql+psycopg://u:p@h/postgres"
    assert _normalize_url("sqlite:///./phishlens.db") == "sqlite:///./phishlens.db"


def test_a_raw_at_sign_in_the_password_is_encoded():
    # Render failed with "failed to resolve host 'h@i@s@h@_@aws-0-...'" on exactly this input: libpq
    # reads everything before the LAST '@' as userinfo, so the password leaked into the host name.
    raw = "postgresql://postgres.abc:p@ss@word@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
    assert _normalize_url(raw) == (
        "postgresql+psycopg://postgres.abc:p%40ss%40word@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
    )


def test_an_already_encoded_password_is_not_double_encoded():
    assert _normalize_url("postgresql://u:p%40ss@h:6543/postgres") == "postgresql+psycopg://u:p%40ss@h:6543/postgres"
