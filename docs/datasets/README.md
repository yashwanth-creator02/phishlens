# Dataset card and corpus guide

## Sources and upstream URLs

Both corpora are fetched by `backend/training/download_datasets.py`; no manual download is needed.

1. **Phishing**: Nazario Phishing Corpus, <https://monkey.org/~jose/phishing/>. Upstream stopped shipping one
   tarball, so the fetcher pulls every published per-year file: `phishing0.mbox`, `20051114.mbox`,
   `phishing1.mbox`, `phishing2.mbox`, `phishing3.mbox`, and `phishing-2015` through `phishing-2025` (the latest
   year upstream has, published 2026-02-19). `private-phishing4` is deliberately excluded: it contains
   donor-private messages. `20051114.mbox` overlaps the 2005 mboxes; the loader dedupes on raw hash,
   Message-ID, and body hash, so the overlap does not inflate the dataset.
2. **Legitimate**: Apache SpamAssassin Public Corpus, <https://spamassassin.apache.org/old/publiccorpus/>.
   The fetcher pulls `20030228_easy_ham.tar.bz2` and `20030228_hard_ham.tar.bz2`.

Neither host serves an API, so the fetcher treats both as plain HTTPS downloads, verifies nothing upstream, and
records SHA-256 per file locally in `backend/data/raw/<name>/manifest.json`.

## Licences and terms

Public research corpora provided under their respective academic and open research terms. Do not redistribute them
commercially, and do not commit them. Any real message in either corpus is a historical sample, not live mail.

## Sizes and statistics

- Nazario: **4,306 phishing messages after dedupe** (measured 2026-11-10), from 12 published files: `phishing0`,
  `20051114`, `phishing1`, `phishing2`, `phishing3`, and `phishing-2015` to `phishing-2025`. The five files fetched
  before the 2026-11-10 expansion (`phishing0`, `phishing1`, `phishing2`, `phishing-2024`, `phishing-2025`) parsed to
  2,182 messages; that smaller set is what the committed evaluation and the promoted model were trained on.
- SpamAssassin: 2,712 legitimate messages across `easy_ham` (2,500) and `hard_ham` (250), of which 633 carry the
  `spamassassin.taint.org` sender domain and are excluded from evaluation and training (see
  [17-real-corpus-evaluation.md](../17-real-corpus-evaluation.md) "Artefacts").
- Totals in hand after dedupe: **7,018 messages** (4,306 phishing + 2,712 legitimate) before the taint exclusion.
  The committed numbers in `reports/` predate this expansion and have not been recomputed.
- Exact counts and SHA-256 checksums are written to `backend/data/raw/<name>/manifest.json` by the fetcher.

## Kaggle corpora

`backend/training/download_kaggle.py` fetches Kaggle datasets that ship as CSV with the email split across
columns, and rebuilds one `.eml` per row so the same feature extractor can read them:

```powershell
cd backend
python -m training.download_kaggle                       # all supported datasets
python -m training.download_kaggle --names ceas08        # one dataset
```

| Dataset | Kaggle ref | Rows | Phishing | Legitimate | Era |
|---|---|---:|---:|---:|---|
| `ceas08` | `naserabdullahalam/phishing-email-dataset` (`CEAS_08.csv`) | 39,154 | 20,874 | 17,293 | 2008 |
| `nigerian-fraud` | same archive (`Nigerian_Fraud.csv`) | 3,332 | 2,720 | 0 | 2002-2003 |
| `spamassassin-kaggle` | same archive (`SpamAssasin.csv`) | 5,809 | 1,701 | 4,087 | 2002-2003 |

The counts are what the converter produced on 2026-11-12; each run writes `summary.json` next to the messages.
The rows that are skipped are counted too: 987 for CEAS (mostly a sender the header parser cannot read) and 612 for
the 419 scams (mostly a date the platform's timestamp conversion rejects).

**Kaggle's public download endpoint serves these datasets without an API token.** The CSV inside the archive is
verified against a recorded SHA-256 before anything is written. The zip itself is not gated on a hash, because
Kaggle may repack it at any time.

### Which Kaggle datasets are usable, and why the others are not

The obvious Kaggle phishing datasets fall into four groups, and only the first can feed this pipeline:

- **Rows with real header fields** (sender, receiver, date, subject, body): usable. CEAS 2008 and the Nigerian
  419 scams are in this group and are supported.
- **Rows with tokenised bodies** (`zefang-liu/phishing-email-dataset`, `subhajournal/phishingemails`): not usable.
  The body has been shredded into words, so `http://example.com` becomes `http example com`, and there is no
  From, no Date and no Subject. A message rebuilt from one of these would report every header as absent, which
  is a false fact about the mail.
- **Pre-computed feature tables** (`ethancratchley/email-phishing-dataset`, `akashsurya156/phishing-paper1`): not
  usable. These hold 500,000+ rows of already-extracted numbers, with no raw message behind them.
- **LLM-generated text** (`kuladeep19/phishing-and-legitimate-emails-dataset`): not usable. The rows carry a
  `Keywords:` annotation and an invented signature, so they are synthetic data dressed as a corpus.

Two datasets that looked promising were rejected after inspection: `avnbluefox/avn-phishing-email-classification-dataset`
is CEAS 2008 again (all 34,620 of its distinct bodies are in CEAS) plus 402 rows of synthetic garbage with dates
like `2025/99/99`; `rashedsarad/ham-and-spam-emails-with-attachments` has 2023-era spam but no body text, only
counts of words and punctuation.

### What the conversion does and does not do

- Only headers the row actually carries are written. A row with no `Authentication-Results` gets no such header,
  so the extractor reports authentication as *missing*, never as *failed*.
- The `urls` column is a count, not a list. The links live in the body, so the body is carried over unchanged.
- A row without a sender, a date or a subject is skipped. Writing a message with no `From` would teach the model
  that a missing sender is normal, which is a different fact from "the header said nothing".
- Each output file is named after the hash of its content, and the output directory is cleared first. Without
  that, a change to the conversion leaves the previous messages behind and a re-run mixes two conversions.

The Kaggle corpora are 2002-2008 material. They add phishing diversity, not modern phishing: the corpus dates
are the same era as SpamAssassin, which is the era the released model already handles. What they do not add is a
single message from the 2015-2025 campaigns. The measured effect is in
[21](../21-modern-corpus-evaluation-plan.md) section 15.

## Phishing Pot corpus

`backend/training/download_phishing_pot.py` fetches the Phishing Pot corpus (`rf-peixoto/phishing_pot`, <https://github.com/rf-peixoto/phishing_pot.git>), which contains real phishing samples collected via honeypots:

```powershell
cd backend
python -m training.download_phishing_pot --since-year 2022
```

- **Licence**: CC BY-NC 4.0 (Attribution-NonCommercial). Non-commercial academic use is permitted with required attribution.
- **Date-header filter**: Filters out messages without a valid Date header or whose year is older than `--since-year` (default 2022).
- **Shortcut masking**: Replaces every occurrence of `phishing@pot` with `user@example.com` in raw message bytes to prevent the model from learning the upstream contributor's address rewrite as a class giveaway.

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
