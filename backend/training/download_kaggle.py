"""Download Kaggle phishing corpora and rebuild them as real ``.eml`` messages.

Several widely used Kaggle phishing datasets ship as CSV with the email split across columns
(``sender``, ``receiver``, ``date``, ``subject``, ``body``, ``urls``, ``label``) instead of as
raw messages. The feature extractor reads raw messages, so this module rebuilds one ``.eml``
per row from exactly the fields the CSV carries.

Two rules make the rebuilt corpus honest:

* Only headers the source actually provides are written. A row with no ``Authentication-Results``
  gets no such header, so the extractor reports authentication as *missing*, not as *failed*.
* The ``urls`` column is a count, not a list. The links live in the body, so the body is carried
  over unchanged rather than being rebuilt from the count.

Rows without the fields needed to form a message are skipped rather than filled in. Writing a
message with no ``From`` would teach the model that a missing sender is normal, which is a
different fact from "the header said nothing".

Kaggle's public download endpoint serves these datasets without an API token. The CSV inside the
archive is verified against a recorded SHA-256 before anything is written: the zip itself may be
repackaged by Kaggle at any time, so the archive hash is not a stable thing to gate on.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.request
import zipfile
from email.message import EmailMessage
from email.utils import formatdate, parseaddr, parsedate_to_datetime
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RAW_DIR = BACKEND_DIR / "data" / "raw" / "kaggle"

csv.field_size_limit(300 * 1024 * 1024)

# Only datasets whose rows carry real header fields belong here. A dataset of tokenised bodies
# has no From, no Date and no Subject, so a message rebuilt from it would misreport all three.
DATASETS: dict[str, dict] = {
    "ceas08": {
        "ref": "naserabdullahalam/phishing-email-dataset",
        "csv": "CEAS_08.csv",
        "label_column": "label",
        "csv_sha256": "22375e7d5f5a8229dbe987914ee9b3705656c590038662a7df6054629b376074",
        "note": "CEAS 2008 phishing challenge, 39,154 rows with sender, date, subject and body",
    },
    "nigerian-fraud": {
        "ref": "naserabdullahalam/phishing-email-dataset",
        "csv": "Nigerian_Fraud.csv",
        "label_column": "label",
        "csv_sha256": "f5d6930763cae6feeae6484131c79655a7440abbb97d6f51eab757aea4e6ab4b",
        "note": "Nigerian 419 scam emails, 3,332 rows, all phishing",
    },
    "spamassassin-kaggle": {
        "ref": "naserabdullahalam/phishing-email-dataset",
        "csv": "SpamAssasin.csv",
        "label_column": "label",
        "csv_sha256": "3bfe8f8abff89f69a98456be50413c2fcb20a476141116dd84ee1507b980c00e",
        "note": "SpamAssassin messages with headers, 5,809 rows. Overlaps the SpamAssassin tarball "
                "already fetched from spamassassin.apache.org, and is 2003 material.",
    },
}

# A row without these cannot become a message: the extractor would read the sender domain as
# unknown, and an unknown sender is a different fact from a missing header.
REQUIRED_FIELDS = ("sender", "date", "subject")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(ref: str) -> bytes:
    url = f"https://www.kaggle.com/api/v1/datasets/download/{ref}"
    req = urllib.request.Request(url, headers={"User-Agent": "PhishLens-dataset/1.0"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return resp.read()


def _normalise_date(value: str) -> str | None:
    """Return an RFC 2822 date, or None when the source date cannot be read.

    The corpus contains a date in the year 102, which is outside the range the platform's
    timestamp conversion accepts. Such a date is treated as unreadable rather than crashing the
    run: the message is kept, with no Date header, and the extractor reports it as undated.
    """
    value = (value or "").strip()
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if dt is None or dt.year < 1970 or dt.year > 2100:
        return None
    try:
        return formatdate(dt.timestamp())
    except (OSError, OverflowError, ValueError):
        return None


def _normalise_sender(value: str) -> str | None:
    """Return a sender the header parser can read, or None when there is no usable address.

    Two shapes in the corpus break the standard header parser: a display name that is only
    punctuation (``..... <user@host>``), and a display name that starts with a dot
    (``".NET Buyer's Guide" <user@host>``). The address is the fact that matters here, so the
    display name is dropped in both cases rather than being carried into a header that cannot be
    parsed.
    """
    value = (value or "").strip()
    if not value:
        return None
    name, addr = parseaddr(value)
    # parseaddr reads a bare word as an address, so the address has to look like one. Without
    # this, a free-text sender such as "no address here" becomes the address "no".
    if not addr or "@" not in addr:
        return None
    if not name or not any(ch.isalnum() for ch in name) or name.startswith("."):
        return addr
    return f"{name} <{addr}>"


def _safe_header(value: str) -> str | None:
    """Return a header value the serializer can write, or None when it cannot be represented.

    The corpus carries header values that the standard encoder rejects: a subject that is a raw
    Big5 encoded-word whose payload is corrupt, and subjects with characters outside the
    encodable range. A value that cannot be written is dropped rather than being forced through,
    because a mangled header would be a false fact about the message.
    """
    value = (value or "").strip()
    if not value:
        return None
    if value.isascii():
        return value
    # A value that is already an encoded word is kept as text: re-encoding it would only hide
    # that the original charset cannot be decoded.
    if value.startswith("=?"):
        return value
    try:
        value.encode("utf-8").decode("utf-8")
    except UnicodeEncodeError:
        return None
    return value


def _clean_body(value: str) -> str:
    """Strip characters that cannot appear in a message body.

    A source body may carry an encoded attachment part, and a raw NUL or a lone control character
    makes the message unserialisable. Those bytes carry no text, so they are removed rather than
    being escaped into the message.
    """
    value = (value or "").replace("\x00", "")
    return "".join(ch for ch in value if ch in "\t\n\r" or ord(ch) >= 32)


def build_message(row: dict) -> bytes | None:
    """Rebuild one raw message from a CSV row, or None when the row cannot carry a message."""
    if any(not (row.get(field) or "").strip() for field in REQUIRED_FIELDS):
        return None
    sender = _normalise_sender(row.get("sender") or "")
    if sender is None:
        return None
    msg = EmailMessage()
    msg["From"] = sender
    receiver = _safe_header((row.get("receiver") or "").strip())
    if receiver:
        try:
            msg["To"] = receiver
        except (UnicodeEncodeError, ValueError):
            pass
    subject = _safe_header((row.get("subject") or "").strip())
    if subject:
        try:
            msg["Subject"] = subject
        except (UnicodeEncodeError, ValueError):
            pass
    date = _normalise_date(row.get("date") or "")
    if date:
        msg["Date"] = date
    msg["MIME-Version"] = "1.0"
    try:
        msg.set_content(_clean_body(row.get("body") or ""))
    except (OSError, ValueError, UnicodeEncodeError):
        # A body the MIME encoder cannot serialise carries no usable text for the extractor.
        return None
    try:
        return msg.as_bytes()
    except (UnicodeEncodeError, ValueError):
        return None


def convert(rows, label_column: str, out_dir: Path) -> dict:
    """Write one .eml per usable row, split into a phishing and a legitimate directory.

    The output directory is cleared first. Each file is named after the hash of its content, so a
    change to the conversion leaves the previously written messages behind, and a re-run would
    then mix two different conversions in one corpus.
    """
    counts = {"phishing": 0, "legitimate": 0, "skipped": 0}
    for folder in ("phishing", "legitimate"):
        stale = out_dir / folder
        if stale.is_dir():
            for old in stale.glob("*.eml"):
                old.unlink()
        else:
            stale.mkdir(parents=True, exist_ok=True)
    for row in rows:
        raw = build_message(row)
        if raw is None:
            counts["skipped"] += 1
            continue
        label = (row.get(label_column) or "").strip()
        if label in ("1", "1.0"):
            folder, key = "phishing", "phishing"
        elif label in ("0", "0.0"):
            folder, key = "legitimate", "legitimate"
        else:
            counts["skipped"] += 1
            continue
        target = out_dir / folder
        target.mkdir(parents=True, exist_ok=True)
        name = hashlib.sha256(raw).hexdigest()[:24]
        (target / f"{name}.eml").write_bytes(raw)
        counts[key] += 1
    return counts


def _csv_member(archive: bytes, member: str) -> bytes:
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as z:
            with z.open(member) as raw:
                return raw.read()
    except (zipfile.BadZipFile, KeyError) as exc:
        raise SystemExit(f"the downloaded archive does not contain {member}: {exc}") from exc


def ingest(name: str, raw_dir: Path, verify_sha: bool = True) -> dict:
    """Download, verify and convert one Kaggle dataset. Returns a summary."""
    spec = DATASETS[name]
    dest = raw_dir / name
    dest.mkdir(parents=True, exist_ok=True)
    blob = _download(spec["ref"])
    payload = _csv_member(blob, spec["csv"])
    digest = _sha256(payload)
    if verify_sha and spec["csv_sha256"] != digest:
        raise SystemExit(f"{name}: {spec['csv']} sha256 {digest} does not match the recorded manifest; "
                         f"refusing to use it")

    with io.TextIOWrapper(io.BytesIO(payload), encoding="utf-8", errors="replace") as text:
        reader = csv.DictReader(text)
        counts = convert(reader, spec["label_column"], dest)
    summary = {
        "name": name,
        "source": spec["ref"],
        "csv": spec["csv"],
        "note": spec["note"],
        "csv_sha256": digest,
        "counts": counts,
    }
    (dest / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=DEFAULT_RAW_DIR, help="raw data root")
    ap.add_argument("--names", nargs="*", default=list(DATASETS), help="datasets to ingest")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip the checksum check (only when a manifest was updated by hand)")
    args = ap.parse_args(argv)
    out = {}
    for name in args.names:
        if name not in DATASETS:
            raise SystemExit(f"unknown dataset: {name!r} (known: {sorted(DATASETS)})")
        summary = ingest(name, args.out, verify_sha=not args.no_verify)
        out[name] = summary
        print(f"{name}: {summary['counts']} csv_sha256={summary['csv_sha256'][:12]}")
    return out


if __name__ == "__main__":
    main()
