"""Audit a trained model directory for personal data before it is published or deployed.

The model artifact is a tree ensemble over 65 aggregate features, so it should contain no
addresses, subjects, body text or sender domains. This script proves that instead of asserting
it: it reads the sender domains from the personal mailbox itself, then looks for any of them,
plus any email-address pattern, in every file of the model directory.

The report also states whether the model was fitted on personal mail. That is provenance, not
leakage, and it is what decides whether the artifact may be published at all: a model fitted on
one person's inbox is a derivative of that inbox, so it is published only on the owner's
explicit decision and only after this script reports the artifact clean.

Usage:
    python -m scripts.audit_model --model models/active --mailbox "data/raw/mailbox"
    python -m scripts.audit_model --model models/active --mailbox "data/raw/mailbox" --json

Exit code 0 = the artifact contains no personal data, 1 = personal data found, 2 = the audit
could not run.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
import zlib
from pathlib import Path

ADDRESS = re.compile(
    # A well-formed address: a local part of at least two characters, a lowercase TLD, and no
    # address character directly beside the match. The stricter shape matters because a binary
    # model file contains random bytes, and a loose pattern flags those as addresses.
    r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]{2,}@[A-Za-z0-9-]{1,63}\.[a-z]{2,24}(?![A-Za-z0-9-])"
)
ADDRESS_HEADERS = ("from:", "reply-to:", "return-path:", "sender:", "to:", "cc:", "bcc:", "delivered-to:")
TOKEN = re.compile(r"[a-z0-9]{6,}")


def mailbox_domains(mailbox: Path) -> set[str]:
    """Domains that appear in the personal mailbox, read straight from the export.

    Every address-bearing header is read, not just From, because a domain can appear only in
    Reply-To or Return-Path and would then be invisible to a narrower scan.
    """
    domains: set[str] = set()
    for mbox in sorted(mailbox.rglob("*.mbox")):
        try:
            with open(mbox, "rb") as handle:
                for raw in handle:
                    line = raw.decode("utf-8", errors="ignore").strip()
                    if not line.lower().startswith(ADDRESS_HEADERS):
                        continue
                    for match in ADDRESS.findall(line):
                        domains.add(match.split("@")[-1].lower())
        except OSError:
            continue
    return domains


def mailbox_subject_tokens(mailbox: Path, limit: int = 400) -> set[str]:
    """Distinctive words from the mailbox subject lines, to catch leaked subject text.

    A model artifact should contain no subject text either, not only no addresses. Rare tokens
    are used, because a common word like "invoice" would trip on an unrelated string. Tokens that
    also occur in the project's own source are skipped: those are the model's vocabulary, not the
    owner's mail.
    """
    counts: dict[str, int] = {}
    for mbox in sorted(mailbox.rglob("*.mbox")):
        try:
            with open(mbox, "rb") as handle:
                for raw in handle:
                    line = raw.decode("utf-8", errors="ignore")
                    if not line.lower().startswith("subject:"):
                        continue
                    for token in TOKEN.findall(line.lower()):
                        counts[token] = counts.get(token, 0) + 1
        except OSError:
            continue
    vocabulary = _project_vocabulary()
    tokens = {t for t, n in counts.items() if n <= 3 and t not in vocabulary}
    # Keep the scan bounded: the rarest tokens are the most identifying.
    return set(sorted(tokens, key=lambda t: (counts[t], t))[:limit])


def _project_vocabulary() -> set[str]:
    """Words the project's own source uses, so they are not treated as leaked mail text."""
    root = Path(__file__).resolve().parents[1]
    words: set[str] = set()
    for path in list(root.glob("app/**/*.py")) + list(root.glob("training/*.py")):
        try:
            words.update(TOKEN.findall(path.read_text(encoding="utf-8", errors="ignore").lower()))
        except OSError:
            continue
    return words


def _decodings(blob: bytes) -> list[str]:
    """Every text view of a file worth searching: plain, UTF-16, gzip, zlib and base64."""
    views = [blob.decode("utf-8", errors="ignore"), blob.decode("utf-16", errors="ignore")]
    for decomp in (gzip.decompress, zlib.decompress):
        try:
            views.append(decomp(blob).decode("utf-8", errors="ignore"))
        except Exception:
            pass
    try:
        views.append(base64.b64decode(blob, validate=False).decode("utf-8", errors="ignore"))
    except Exception:
        pass
    return views


def audit(model_dir: Path, domains: set[str], tokens: set[str] | None = None) -> dict:
    findings: list[dict] = []
    checked: list[str] = []
    tokens = tokens or set()
    for path in sorted(model_dir.rglob("*")):
        if not path.is_file():
            continue
        checked.append(path.name)
        blob = path.read_bytes()
        for text in _decodings(blob):
            lowered = text.lower()
            for domain in sorted(domains):
                if domain in lowered:
                    findings.append({"file": path.name, "kind": "sender_domain", "value": domain})
            for match in set(ADDRESS.findall(text)):
                findings.append({"file": path.name, "kind": "email_address", "value": match})
            words = set(TOKEN.findall(lowered))
            for token in sorted(tokens & words):
                findings.append({"file": path.name, "kind": "subject_token", "value": token})
    meta_path = model_dir / "meta.json"
    meta: dict = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, ValueError):
            meta = {}
    training = meta.get("training") or {}
    return {
        "model_dir": str(model_dir),
        "files_checked": checked,
        "domains_checked": len(domains),
        "subject_tokens_checked": len(tokens),
        # Provenance, not leakage: the model was fitted on mail the owner supplied. It is reported
        # because it must be declared, and because a model fitted on personal mail is only ever
        # published with the owner's explicit decision.
        "trained_on_personal_data": bool(training.get("contains_personal_data")),
        "background_rows_personal": training.get("background_rows_personal"),
        "findings": findings,
        # The gate for publication is the artifact: no sender domain, no address and no distinctive
        # subject word may appear in any file of the model directory.
        "clean": not findings,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, help="model directory to audit")
    ap.add_argument("--mailbox", required=True, help="personal mailbox directory or file")
    ap.add_argument("--json", action="store_true", help="print the raw report as JSON")
    args = ap.parse_args(argv)

    model_dir = Path(args.model)
    if not model_dir.exists():
        print(f"model directory not found: {model_dir}", file=sys.stderr)
        return 2
    mailbox = Path(args.mailbox)
    if not mailbox.exists():
        print(f"mailbox not found: {mailbox}", file=sys.stderr)
        return 2

    domains = mailbox_domains(mailbox)
    if not domains:
        print(f"no sender domains read from {mailbox}; the audit would be meaningless", file=sys.stderr)
        return 2

    tokens = mailbox_subject_tokens(mailbox)
    report = audit(model_dir, domains, tokens)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"model: {report['model_dir']}")
        print(f"files checked: {', '.join(report['files_checked']) or 'none'}")
        print(f"sender domains checked: {report['domains_checked']}")
        print(f"subject tokens checked: {report['subject_tokens_checked']}")
        print(f"fitted on personal mail: {report['trained_on_personal_data']}")
        print(f"personal rows in the SHAP background: {report['background_rows_personal']}")
        if report["clean"]:
            print("result: CLEAN, no sender domain, address or subject word found in any model file")
        else:
            print(f"result: {len(report['findings'])} FINDINGS")
            for finding in report["findings"]:
                print(f"  {finding['file']}: {finding['kind']} {finding['value']}")
    return 0 if report["clean"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
