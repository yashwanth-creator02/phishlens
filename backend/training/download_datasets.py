"""Prepare and process already-downloaded local raw email corpora (Nazario phishing, SpamAssassin ham).

Writes raw .eml files to backend/data/raw/<name>/ and generates a manifest
containing counts, file paths, and SHA-256 checksums, with deduplication
by Message-ID and body hash. Note: Upstream raw corpora (Nazario and SpamAssassin)
must be downloaded manually due to academic repository hosting limits.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from app.ingestion.email_parser import parse_email


def calculate_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def process_corpus_dir(src_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    seen_message_ids: set[str] = set()
    seen_body_hashes: set[str] = set()
    manifest_entries = []

    for f in sorted(src_dir.rglob("*")):
        if f.is_dir():
            continue
        if f.suffix.lower() in (".eml", ".txt", "") or f.name.endswith(".mbox"):
            try:
                raw = f.read_bytes()
                parsed = parse_email(raw)
            except Exception:
                continue

            mid = parsed.message_id or ""
            body_hash = calculate_sha256(parsed.body_plain.encode("utf-8", errors="ignore"))

            if mid and mid in seen_message_ids:
                continue
            if body_hash in seen_body_hashes:
                continue

            if mid:
                seen_message_ids.add(mid)
            seen_body_hashes.add(body_hash)

            file_sha256 = calculate_sha256(raw)
            dest_name = f"{file_sha256[:16]}.eml"
            dest_path = out_dir / dest_name
            dest_path.write_bytes(raw)

            manifest_entries.append({
                "filename": dest_name,
                "sha256": file_sha256,
                "size": len(raw),
                "from_domain": parsed.from_domain,
            })

    manifest = {
        "count": len(manifest_entries),
        "files": manifest_entries,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--phish-src", type=Path, default=Path("backend/data/raw/nazario_src"))
    ap.add_argument("--ham-src", type=Path, default=Path("backend/data/raw/spamassassin_src"))
    ap.add_argument("--out", type=Path, default=Path("backend/data/raw"))
    args = ap.parse_args(argv)

    phish_out = args.out / "nazario"
    ham_out = args.out / "spamassassin"

    manifests = {}
    if args.phish_src.exists():
        manifests["phish"] = process_corpus_dir(args.phish_src, phish_out)
    if args.ham_src.exists():
        manifests["ham"] = process_corpus_dir(args.ham_src, ham_out)
    print("Corpus preparation and manifest generation complete:", list(manifests.keys()))
    return manifests


if __name__ == "__main__":
    main()
