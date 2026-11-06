from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from urllib.parse import quote

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

from .models import Base


def _normalize_url(url: str) -> str:
    # Supabase hands out postgresql:// strings; only the psycopg3 driver is installed
    if not url.startswith(("postgresql://", "postgres://")):
        return url
    rest = url.split("://", 1)[1]
    # libpq splits userinfo at the last '@', so a raw '@' in the password turns part of the password
    # into the host name. Re-encode the password when the userinfo contains more than one '@'.
    creds, sep, host = rest.rpartition("@")
    if sep and "@" in creds:
        user, _, password = creds.partition(":")
        rest = f"{user}:{quote(password, safe='')}@{host}"
    return "postgresql+psycopg://" + rest


@lru_cache
def get_engine():
    url = _normalize_url(get_settings().database_url)
    kwargs = {"connect_args": {"check_same_thread": False}} if url.startswith("sqlite") else {"pool_pre_ping": True}
    return create_engine(url, **kwargs)


@lru_cache
def get_sessionmaker():
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(get_engine())


def get_db() -> Iterator[Session]:
    db = get_sessionmaker()()
    try:
        yield db
    finally:
        db.close()
