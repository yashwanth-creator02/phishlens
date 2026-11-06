# Dataset card and corpus guide

## Sources and upstream URLs

Both corpora are fetched by `backend/training/download_datasets.py`; no manual download is needed.

1. **Phishing**: Nazario Phishing Corpus, <https://monkey.org/~jose/phishing/>. Upstream stopped shipping one
   tarball, so the fetcher pulls the per-year mbox files `phishing0.mbox`, `phishing1.mbox`, `phishing2.mbox`,
   plus the `phishing-2024` and `phishing-2025` archives (about 7,000 raw messages) so the set spans both the
   2003-2007 mboxes and contemporary campaigns. `private-phishing4` is deliberately excluded: it contains
   donor-private messages.
2. **Legitimate**: Apache SpamAssassin Public Corpus, <https://spamassassin.apache.org/old/publiccorpus/>.
   The fetcher pulls `20030228_easy_ham.tar.bz2` and `20030228_hard_ham.tar.bz2`.

Neither host serves an API, so the fetcher treats both as plain HTTPS downloads, verifies nothing upstream, and
records SHA-256 per file locally in `backend/data/raw/<name>/manifest.json`.

## Licences and terms

Public research corpora provided under their respective academic and open research terms. Do not redistribute them
commercially, and do not commit them. Any real message in either corpus is a historical sample, not live mail.

## Sizes and statistics

- Nazario: 2,182 phishing messages after dedupe, from five mbox/archives (`phishing0`, `phishing1`, `phishing2`,
  `phishing-2024`, `phishing-2025`).
- SpamAssassin: 2,712 legitimate messages across `easy_ham` (2,500) and `hard_ham` (250), of which 633 carry the
  `spamassassin.taint.org` sender domain and are excluded from evaluation and training (see
  [17-real-corpus-evaluation.md](../17-real-corpus-evaluation.md) "Artefacts").
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

The fetcher is rerunnable, per source file: a source is downloaded only when neither the file nor an
already-extracted equivalent is on disk, so adding a new yearly archive later fetches only that archive.
Evaluation trains its own comparator model in memory and writes `reports/evaluation.json` plus `reports/evaluation.md`;
it never overwrites the serving model in `backend/models/`. Both the fetcher's manifest writer and
`training.corpus.load_dir` treat every non-archive, non-manifest file as corpus content (SpamAssassin ships
hash-named files with no extension), so do not reintroduce an extension filter there.

## Note on git

Raw email datasets (`backend/data/raw/`) and trained models (`backend/models/`) are gitignored and must never be
committed. The committed evidence is the metrics report, not the messages.
