"""Download and preprocess the Phishing Pot corpus (rf-peixoto/phishing_pot).

Upstream repository: https://github.com/rf-peixoto/phishing_pot.git
Licence: CC BY-NC 4.0 (Attribution-NonCommercial).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
import email
import email.policy
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = BACKEND_DIR / "data" / "raw"
SOURCE_URL = "https://github.com/rf-peixoto/phishing_pot.git"
ARCHIVE_URL = "https://github.com/rf-peixoto/phishing_pot/archive/refs/heads/main.tar.gz"
BACKUP_ARCHIVE_URL = "https://github.com/rf-peixoto/phishing_pot/archive/refs/heads/master.tar.gz"

IGNORED_NAMES = {"readme.md", "license", "licence", "manifest.json", "summary.json", ".gitignore"}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "PhishLens-dataset/1.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1024 * 1024):
            fh.write(chunk)


def parse_message_date(raw: bytes) -> datetime | None:
    """Parse an RFC 2822 Date header into an aware UTC datetime, or None."""
    try:
        msg = email.message_from_bytes(raw, policy=email.policy.default)
        date_str = msg.get("Date")
        if not date_str:
            return None
        dt = parsedate_to_datetime(date_str)
        if dt is None:
            return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except Exception:
        return None


def process_corpus(src_dir: Path, dest_dir: Path, since_year: int = 2022) -> dict:
    """Filter raw messages by Date header >= since_year, mask phishing@pot, and write manifest."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for old in dest_dir.glob("**/*.eml"):
        old.unlink()

    counts = {
        "parsed": 0,
        "kept": 0,
        "dropped_undated": 0,
        "dropped_unparseable": 0,
        "dropped_too_old": 0,
        "masked_files": 0,
        "per_year": {},
    }
    files_manifest = []

    for f in sorted(src_dir.rglob("*")):
        if not f.is_file():
            continue
        if f.name.lower() in IGNORED_NAMES or f.name.startswith("."):
            continue
        if f.suffix.lower() not in (".eml", ".txt", ""):
            continue

        try:
            raw = f.read_bytes()
        except OSError:
            continue

        try:
            msg = email.message_from_bytes(raw, policy=email.policy.default)
            date_str = msg.get("Date")
        except Exception:
            counts["dropped_unparseable"] += 1
            continue

        if not date_str:
            counts["dropped_undated"] += 1
            continue

        dt = parse_message_date(raw)
        if dt is None:
            counts["dropped_unparseable"] += 1
            continue

        counts["parsed"] += 1
        year = dt.year
        if year < since_year:
            counts["dropped_too_old"] += 1
            continue

        counts["kept"] += 1
        counts["per_year"][str(year)] = counts["per_year"].get(str(year), 0) + 1

        masked = raw.replace(b"phishing@pot", b"user@example.com")
        if masked != raw:
            counts["masked_files"] += 1

        rel_path = f.relative_to(src_dir)
        out_path = dest_dir / rel_path
        if out_path.suffix.lower() not in (".eml", ".txt"):
            out_path = out_path.with_suffix(out_path.suffix + ".eml")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(masked)

        files_manifest.append({
            "path": out_path.relative_to(dest_dir).as_posix(),
            "size": len(masked),
            "sha256": _sha256(masked),
            "original_year": year,
        })

    manifest = {
        "source_url": SOURCE_URL,
        "since_year": since_year,
        "counts": counts,
        "files": files_manifest,
    }
    (dest_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def download_phishing_pot(out_dir: Path = DEFAULT_RAW_DIR, since_year: int = 2022, dry_run: bool = False) -> dict:
    dest = out_dir / "phishing_pot"
    manifest_path = dest / "manifest.json"
    if manifest_path.exists() and not dry_run:
        print(f"phishing_pot: already present at {dest}, skipping download (idempotent).")
        return json.loads(manifest_path.read_text())

    if dry_run:
        print(f"[dry-run] would download {ARCHIVE_URL} -> {dest}")
        return {"dry_run": True, "url": ARCHIVE_URL, "dest": str(dest)}

    dest.mkdir(parents=True, exist_ok=True)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_str:
        tmp_dir = Path(tmp_str)
        archive_path = tmp_dir / "phishing_pot.tar.gz"
        try:
            _fetch(ARCHIVE_URL, archive_path)
        except Exception:
            print(f"Primary archive URL failed, trying backup: {BACKUP_ARCHIVE_URL}")
            _fetch(BACKUP_ARCHIVE_URL, archive_path)

        extract_dir = tmp_dir / "extracted"
        extract_dir.mkdir()
        with tarfile.open(archive_path, mode="r:*") as tf:
            for member in tf.getmembers():
                if member.name.startswith("/") or ".." in member.name:
                    continue
                tf.extract(member, extract_dir, filter="data")

        subdirs = [p for p in extract_dir.iterdir() if p.is_dir()]
        corpus_src = subdirs[0] if len(subdirs) == 1 else extract_dir

        manifest = process_corpus(corpus_src, dest, since_year=since_year)
        return manifest


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_RAW_DIR, help="raw data root")
    ap.add_argument("--since-year", type=int, default=2022, help="keep messages from this year onwards")
    ap.add_argument("--dry-run", action="store_true", help="print plan, no network/writes")
    args = ap.parse_args(argv)
    manifest = download_phishing_pot(out_dir=args.out, since_year=args.since_year, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"phishing_pot: kept={manifest['counts']['kept']} masked={manifest['counts']['masked_files']} per_year={manifest['counts']['per_year']}")
    return manifest


if __name__ == "__main__":
    main()
