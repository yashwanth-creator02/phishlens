"""Release a trained candidate into the tracked directory the Docker image bakes.

The repository is public, so a model that ships in it must be free of personal data. This script
is the gate and the copier in one step:

1. Run the audit against the candidate, using the owner's mailbox as the search vocabulary.
2. Refuse to copy anything the audit flags, or a candidate whose metadata says it was fitted on
   personal mail without the explicit acknowledgement.
3. Copy the candidate into `backend/release/<version_tag>/` and write a release note recording the
   audit result, so the decision is auditable after the fact.

Usage:
    python -m scripts.release_model --model models/active --mailbox "data/raw/mailbox"
    python -m scripts.release_model --model models/active --mailbox "data/raw/mailbox" \
        --allow-personal-data --notes "trained on the owner's inbox, audited clean"
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from scripts.audit_model import audit, mailbox_domains, mailbox_subject_tokens

ROOT = Path(__file__).resolve().parents[1]
RELEASE_DIR = ROOT / "release"
ARTIFACTS = ("model.joblib", "calibrator.joblib", "background.npy", "meta.json")

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True, help="candidate model directory to release")
    ap.add_argument("--mailbox", required=True, help="personal mailbox used as the audit vocabulary")
    ap.add_argument("--allow-personal-data", action="store_true",
                    help="release a model that was fitted on personal mail. The audit must still report "
                         "the artifact clean.")
    ap.add_argument("--notes", default="", help="one line recorded in the release note")
    ap.add_argument("--out", default=str(RELEASE_DIR))
    args = ap.parse_args(argv)

    model_dir = Path(args.model)
    if not (model_dir / "meta.json").exists():
        print(f"not a model directory: {model_dir}", file=sys.stderr)
        return 2

    missing = [name for name in ARTIFACTS if name != "calibrator.joblib"
               and not (model_dir / name).exists()]
    if missing:
        print(f"model directory is missing {missing}", file=sys.stderr)
        return 2

    mailbox = Path(args.mailbox)
    domains = mailbox_domains(mailbox)
    tokens = mailbox_subject_tokens(mailbox)
    if not domains:
        print(f"no sender domains read from {mailbox}; the audit would be meaningless", file=sys.stderr)
        return 2

    report = audit(model_dir, domains, tokens)
    if not report["clean"]:
        print(f"audit found {len(report['findings'])} problem(s); refusing to release:", file=sys.stderr)
        for finding in report["findings"]:
            print(f"  {finding['file']}: {finding['kind']} {finding['value']}", file=sys.stderr)
        return 1
    if report["trained_on_personal_data"] and not args.allow_personal_data:
        print("the candidate was fitted on personal mail; pass --allow-personal-data to release it",
              file=sys.stderr)
        return 1

    meta = json.loads((model_dir / "meta.json").read_text())
    tag = meta["version_tag"]
    dest = Path(args.out) / "model"
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for name in ARTIFACTS:
        if (model_dir / name).exists():
            shutil.copy2(model_dir / name, dest / name)

    release = {
        "version_tag": tag,
        "algorithm": meta["algorithm"],
        "trained_at": meta.get("trained_at"),
        "data_source": meta.get("data_source"),
        "n_samples": meta.get("n_samples"),
        "metrics": meta.get("metrics", {}),
        "notes": args.notes,
        "audit": {
            "domains_checked": report["domains_checked"],
            "subject_tokens_checked": report["subject_tokens_checked"],
            "files_checked": report["files_checked"],
            "findings": report["findings"],
            "fitted_on_personal_data": report["trained_on_personal_data"],
            "personal_rows_in_shap_background": report["background_rows_personal"],
        },
    }
    (dest / "release.json").write_text(json.dumps(release, indent=2))
    print(f"released {tag} -> {dest}")
    print(f"audit: {report['domains_checked']} sender domains, "
          f"{report['subject_tokens_checked']} subject words, 0 findings")
    print(f"fitted on personal mail: {report['trained_on_personal_data']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
