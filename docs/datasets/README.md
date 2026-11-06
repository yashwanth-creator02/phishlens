# Dataset card and corpus guide

## Sources and upstream URLs

Both corpora are fetched by `backend/training/download_datasets.py`; no manual download is needed.

1. **Phishing**: Nazario Phishing Corpus, <https://monkey.org/~jose/phishing/>. Upstream stopped shipping one
   tarball, so the fetcher pulls the per-year mbox files `phishing0.mbox` to `phishing2.mbox`.
   `private-phishing4.mbox` is deliberately excluded: it contains donor-private messages.
2. **Legitimate**: Apache SpamAssassin Public Corpus, <https://spamassassin.apache.org/old/publiccorpus/>.
   The fetcher pulls `20030228_easy_ham.tar.bz2` and `20030228_hard_ham.tar.bz2`.

Neither host serves an API, so the fetcher treats both as plain HTTPS downloads, verifies nothing upstream, and
records SHA-256 per file locally in `backend/data/raw/<name>/manifest.json`.

## Licences and terms

Public research corpora provided under their respective academic and open research terms. Do not redistribute them
commercially, and do not commit them. Any real message in either corpus is a historical sample, not live mail.

## Sizes and statistics

- Nazario: roughly 2,000 to 4,000 unique phishing messages after dedupe, depending on how many yearly mboxes are fetched.
- SpamAssassin: about 2,750 legitimate messages across `easy_ham` (2,500) and `hard_ham` (250).
- Exact counts and SHA-256 checksums are written to `backend/data/raw/<name>/manifest.json` by the fetcher.

## Train/test split rule

Dedupe by raw hash, Message-ID, and body-content hash before splitting. The primary evaluation uses a **grouped
split** (`GroupShuffleSplit`): phishing messages are grouped by campaign or first URL host, legitimate messages by
sender domain, so no group appears in both train and test. A random stratified split is reported as a comparison
baseline. Test groups unseen in training are the cold-start slice. Never report the random-split number as the
headline result.

## Corpus preparation

```powershell
cd backend
python -m training.download_datasets              # fetch both corpora into data/raw, write manifests
python -m training.download_datasets --names nazario   # one corpus only
python -m training.download_datasets --dry-run    # print the plan, touch nothing
python -m training.evaluate --phish-dir data/raw/nazario --ham-dir data/raw/spamassassin --out reports
```

The fetcher is rerunnable: when `backend/data/raw/<name>/` already holds `.eml`/`.txt`/`.mbox` files it skips the
network and only regenerates the manifest. Evaluation trains its own comparator model in memory and writes
`reports/evaluation.json` plus `reports/evaluation.md`; it never overwrites the serving model in `backend/models/`.

## Note on git

Raw email datasets (`backend/data/raw/`) and trained models (`backend/models/`) are gitignored and must never be
committed. The committed evidence is the metrics report, not the messages.
