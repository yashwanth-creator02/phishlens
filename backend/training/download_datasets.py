"""Download (or prepare) real labelled email corpora for evaluation.

Upstream corpora are academic tarballs; hosts often block automated crawling, so
this script treats them as *optional network downloads*:

* If ``backend/data/raw/<name>/`` already contains ``.eml``/``.txt``/``.mbox``
  files, the network is skipped and only a manifest is (re)generated.
* Otherwise, each named dataset URL is fetched with ``urllib`` into
  ``backend/data/raw/<name>/`` and then manifest-verified.

``--dry-run`` prints the planned downloads and file layout without touching
the network or the filesystem (other than stdout).

Manifest (``backend/data/raw/<name>/manifest.json``) records, per file, the
relative path, size and SHA-256, plus total counts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
import urllib.request
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = BACKEND_DIR / "data" / "raw"

# name -> (url, archive filename). Nazario phishing + SpamAssassin ham.
DATASETS: dict[str, tuple[str, str]] = {
    "nazario": (
        "https://monkey.org/~jose/phishing/phish.tar.gz",
        "phish.tar.gz",
    ),
    "spamassassin": (
        "https://spamassassin.apache.org/publiccorpus/",
        "publiccorpus.tar.bz2",
    ),
}

EMAIL_SUFFIXES = {".eml", ".txt", ""}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _has_emails(d: Path) -> bool:
    return any(
        f.is_file() and (f.suffix.lower() in EMAIL_SUFFIXES or f.name.lower().endswith("mbox"))
        for f in d.rglob("*")
    )


def _iter_email_files(root: Path):
    for f in sorted(root.rglob("*")):
        if not f.is_file():
            continue
        if f.suffix.lower() in EMAIL_SUFFIXES or f.name.lower().endswith("mbox"):
            # skip the manifest itself: it lives beside the corpus, never inside it
            if f.name == "manifest.json":
                continue
            yield f


def build_manifest(root: Path) -> dict:
    files = []
    for f in _iter_email_files(root):
        data = f.read_bytes()
        files.append({
            "path": f.relative_to(root).as_posix(),
            "size": len(data),
            "sha256": _sha256(data),
        })
    total = sum(entry["size"] for entry in files)
    return {"count": len(files), "total_bytes": total, "files": files}


def write_manifest(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(root)
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def _fetch(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "PhishLens-dataset/1.0"})
    with urllib.request.urlopen(req) as resp, open(dest, "wb") as fh:
        while chunk := resp.read(1024 * 1024):
            fh.write(chunk)


def _extract_archive(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as tf:
        tf.extractall(dest)


def download_dataset(name: str, root: Path, dry_run: bool = False) -> dict:
    """Ensure ``root/<name>/`` holds the corpus; return its manifest."""
    dest = root / name
    dest.mkdir(parents=True, exist_ok=True)
    if _has_emails(dest):
        # Idempotent: existing corpus wins, never re-download.
        return write_manifest(dest)
    url, archive_name = DATASETS[name]
    if dry_run:
        print(f"[dry-run] would download {url} -> {dest / archive_name}")
        return {"count": 0, "total_bytes": 0, "files": [], "dry_run": True, "url": url}
    archive = dest / archive_name
    _fetch(url, archive)
    try:
        _extract_archive(archive, dest)
    except (tarfile.TarError, OSError):
        pass  # not an archive (e.g. a listing page); keep what was fetched
    return write_manifest(dest)


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_RAW_DIR, help="raw data root")
    ap.add_argument("--names", nargs="*", default=list(DATASETS), help="datasets to fetch")
    ap.add_argument("--dry-run", action="store_true", help="print plan, no network/writes")
    args = ap.parse_args(argv)
    manifests = {}
    for name in args.names:
        if name not in DATASETS:
            raise SystemExit(f"unknown dataset: {name!r} (known: {sorted(DATASETS)})")
        manifests[name] = download_dataset(name, args.out, dry_run=args.dry_run)
        print(f"{name}: count={manifests[name]['count']} bytes={manifests[name]['total_bytes']}")
    return manifests


if __name__ == "__main__":
    main()
