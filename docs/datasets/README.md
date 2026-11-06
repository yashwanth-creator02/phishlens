# PhishLens Dataset Card & Corpus Guide

## Sources & Upstream URLs (Manual Download)
1. **Phishing Corpus**: Nazario Phishing Corpus ([http://monkey.org/~jose/phishing/](http://monkey.org/~jose/phishing/) or mirror datasets). Downloading is manual due to upstream hosting constraints.
2. **Legitimate Corpus**: Apache SpamAssassin Public Corpus ([https://spamassassin.apache.org/publiccorpus/](https://spamassassin.apache.org/publiccorpus/)). Downloading is manual.

## Licences & Terms
Public research corpora provided under respective academic and open research licenses. Not for commercial redistribution without upstream attestation.

## Sizes & Statistics
- Target corpus size: ~2,500 - 5,000 samples balanced between phishing and legitimate.
- Exact counts and SHA-256 checksums are recorded in `backend/data/raw/manifest.json` after running the preparation script.

## Train/test split rule

Dedupe by Message-ID and body-content hash before splitting. The primary
evaluation uses a **grouped split** (`GroupShuffleSplit`): phishing messages are
grouped by campaign / first URL host, legitimate messages by sender domain, so
no group appears in both train and test. A random stratified split is reported
as a comparison baseline. Test groups unseen in training are the cold-start
slice. Never report the random-split number as the headline result.

## Corpus Preparation Command
After downloading raw files locally, run:
```powershell
cd backend
python -m training.download_datasets --phish-src <path_to_local_nazario> --ham-src <path_to_local_spamassassin> --out data/raw
python -m training.download_datasets --dry-run   # print the plan, touch nothing
```
`download_datasets.py` skips the network when `backend/data/raw/<name>/`
already holds `.eml`/`.txt`/`.mbox` files and just regenerates the manifest
(counts + SHA-256 per file).

## Important Note on Git
Raw email datasets (`backend/data/raw/`) and extracted models (`backend/models/`) are strictly gitignored (`.gitignore`) and must never be committed to the repository.
