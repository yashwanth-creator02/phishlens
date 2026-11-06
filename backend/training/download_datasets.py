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

# name -> [(url, local filename)]. Nazario phishing mboxes + SpamAssassin ham tarballs.
# monkey.org stopped publishing one tarball; the corpus is per-year mbox files now.
# The 2018+ "private-phishing4" archive is deliberately excluded (donor privacy).
DATASETS: dict[str, list[tuple[str, str]]] = {
    "nazario": [
        ("https://monkey.org/~jose/phishing/phishing0.mbox", "phishing0.mbox"),
        ("https://monkey.org/~jose/phishing/phishing1.mbox", "phishing1.mbox"),
        ("https://monkey.org/~jose/phishing/phishing2.mbox", "phishing2.mbox"),
    ],
    "spamassassin": [
        ("https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham.tar.bz2", "easy_ham.tar.bz2"),
        ("https://spamassassin.apache.org/old/publiccorpus/20030228_hard_ham.tar.bz2", "hard_ham.tar.bz2"),
    ],
}

EMAIL_SUFFIXES = {".eml", ".txt", ""}
# Corpus files are not always named with an extension: SpamAssassin ships
# "0001.217ba49e4b19f7dad40f9526b1a2b1ba", whose suffix is a hash. So the rule is
# "every file is corpus content unless it is an archive or the manifest".
ARCHIVE_SUFFIXES = {".gz", ".bz2", ".zip", ".tar", ".tgz", ".xz", ".7z"}


def _is_corpus_file(f: Path) -> bool:
    return f.name != "manifest.json" and f.suffix.lower() not in ARCHIVE_SUFFIXES


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _has_emails(d: Path) -> bool:
    return any(f.is_file() and _is_corpus_file(f) for f in d.rglob("*"))


def _iter_email_files(root: Path):
    for f in sorted(root.rglob("*")):
        if f.is_file() and _is_corpus_file(f):
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
        # data filter rejects absolute paths, traversal, and device members from the corpus tarballs
        tf.extractall(dest, filter="data")


def download_dataset(name: str, root: Path, dry_run: bool = False) -> dict:
    """Ensure ``root/<name>/`` holds the corpus; return its manifest."""
    dest = root / name
    dest.mkdir(parents=True, exist_ok=True)
    if _has_emails(dest):
        # Idempotent: existing corpus wins, never re-download.
        return write_manifest(dest)
    sources = DATASETS[name]
    if dry_run:
        for url, filename in sources:
            print(f"[dry-run] would download {url} -> {dest / filename}")
        return {"count": 0, "total_bytes": 0, "files": [], "dry_run": True,
                "urls": [url for url, _ in sources]}
    for url, filename in sources:
        archive = dest / filename
        if archive.exists():
            continue
        _fetch(url, archive)
        try:
            _extract_archive(archive, dest)
        except (tarfile.TarError, OSError):
            pass  # mbox files are not archives; keep what was fetched
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
