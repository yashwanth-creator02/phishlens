#!/usr/bin/env python3
"""Delete analyses (and their stored raw emails) older than PHISHLENS_RETENTION_DAYS. Run from backend/ via cron:
    cd backend && python ../scripts/purge_old.py"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.models import Analysis  # noqa: E402
from app.db.session import get_sessionmaker  # noqa: E402

s = get_settings()
cutoff = datetime.utcnow() - timedelta(days=s.retention_days)
with get_sessionmaker()() as db:
    old = db.scalars(select(Analysis).where(Analysis.created_at < cutoff)).all()
    for a in old:
        if a.raw:
            Path(a.raw.storage_path).unlink(missing_ok=True)
        db.delete(a)
    db.commit()
print(f"purged {len(old)} analyses older than {s.retention_days} days")
