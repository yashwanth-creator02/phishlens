# Training methodology and measurements

This page records how the model is trained and what was actually measured. It exists because the model's numbers are
easy to quote and hard to interpret: every figure below says which data it came from and which years, because a false
-positive rate measured on one inbox is not a general false-positive rate.

The method follows an external review of the project. Each section states what was asked for, what was implemented,
and what the result was.

## 1. The question the review raised

The 65-feature contract identifies **the mail provider and the era**, not only the message. A classifier trained to
tell legitimate mail from three different corpora apart recovers the source with **0.981** accuracy (chance 0.333),
and **0.980** using only the 13 header features.

The consequence: a phishing model trained on that feature set can score an unseen inbox on the shape of its provider
rather than on its content, so the measured false-positive rate does not transfer to another person's mail.

Reproduce it:

```powershell
cd backend
python -m scripts.source_leak_test --out ../.tmp/leak
```

The script needs the gitignored corpora, so it is a script and not a pytest case.

## 2. Which features carry the leak

The first version of the test removed one feature at a time. That turned out to be the wrong question: removing any
single feature changed the corpus-recovery accuracy by at most 0.010, because **several features each identify the
corpus on their own**. The leak is redundant.

So the test now also removes a whole class of features at once:

| Feature set removed | Corpus-recovery accuracy (legitimate mail only, 3 corpora) |
|---|---|
| none (baseline) | 0.981 |
| the 13 header features | **0.885** |
| the 18 URL features | 0.981 |
| the 10 text features | 0.980 |
| the 6 action features | 0.982 |
| the 8 attachment features | 0.981 |
| the 10 behavioural features | 0.981 |

The header group is the largest single carrier, and even removing it entirely leaves the corpora recoverable at
0.885. The same pattern holds for the format-only fingerprint (which header names are present, the shape of the Date
and the Message-ID, the charset, the MIME structure, the line endings, the length of the Received chain): it recovers
the corpus at **0.999**, and dropping the MIME block only takes it to 0.988. Dropping the transport headers
(`Received`, `X-Gmail-*`, `ARC-*`, `Authentication-Results`, `Return-Path`) changes nothing at all, which is the
reviewer's point that the leak is deeper than the provider headers.

### What this means

**There is no feature to patch.** The corpora differ in era, provider, MIME structure, encoding and content style all
at once, so any large enough subset of the features identifies which corpus a message came from. The fix is not to
remove features from the model; it is to train on data where the legitimate and the phishing mail come from the same
world, and to measure the false-positive rate on a **second person's** inbox.

The one thing that is cheap and worth doing: CEAS 2008 carries no `Message-ID` and no `Received` chain at all (the
source dataset only kept sender, date, subject and body), so it teaches the model that a message without those
headers is legitimate. The campaign-grouping key and the temporal split now keep it from leaking across partitions,
and `docs/15-risks-and-limitations.md` records the rest.

## 3. The modern phishing corpus

The review asked for a modern phishing corpus, filtered by the message's own `Date` header rather than by file name,
with the contributors' placeholder address masked.

`backend/training/download_phishing_pot.py` does that:

```powershell
cd backend
python -m training.download_phishing_pot --since-year 2022
```

- Source: <https://github.com/rf-peixoto/phishing_pot> (honeypot collector), **CC BY-NC 4.0**. Non-commercial use
  with attribution; see `docs/18-open-manual-actions.md` item 1.
- The filter reads each message's `Date` header. A message with no date, or with a date that does not parse, is
  **dropped** and counted. The file name is never trusted.
- The placeholder `phishing@pot` appears in the phishing class only, so a model would learn it as a giveaway. It is
  replaced with `user@example.com` in the raw bytes before the message is written into the training corpus.
- The manifest records the source, the per-year counts, the number of masked files and a SHA-256 per file.

What it fetched on 2026-11-12: **12,763 messages** kept, 11,834 files masked, per year 2022: 199, 2023: 2,175,
2024: 2,141, 2025: 2,012, 2026: 6,234. (Two messages carry a date in 2031 and 2033, which is a corpus artefact.)

## 4. The split

`--split temporal` in `backend/training/train.py`:

- The oldest mail fits, a later slice validates, the newest tests.
- A **group** is placed by its **earliest** date, so a campaign that spans years never straddles a boundary: the whole
  campaign lands on one side of it.
- Groups with no usable date go to the fit partition. With no date they cannot be the newest mail, and leaving them
  out of the test set is the conservative choice.
- Phishing groups by **campaign**, not by host alone: a distinctive subject wins, and a short or empty subject falls
  back to the link host. Near-duplicate phishing share a subject template but not always a host.

The owner's mailbox is additionally cut at `--legit-until 2026-01-01`, so the 2026 mail is never in the training data.
The published false-positive rate is measured on that 2026 holdout with
`python -m training.evaluate_modern`.

## 5. The operating point

The review asked for the thresholds to come from the validation set and never from the test set. They do:
`operating_points()` in `backend/training/train.py` takes the **raw** validation probabilities, because the isotonic
calibrator is monotone (it cannot change the ranking) and a threshold read off calibrated validation scores would be
measured against the very data the calibrator was fitted on.

It reports, for a false-positive budget of 1% and of 5%, the threshold, the recall and the precision at it, and the
bands those thresholds imply: **HIGH above the 1% threshold, MEDIUM between the two, LOW below the 5% one**. The bands
that ship are a product decision (`BAND_LOW_MAX=29`, `BAND_HIGH_MIN=70`); the report prints the validation-derived
ones next to them so the difference is visible rather than hidden.

## 6. The spread across seeds

`--seeds 7,8,9` runs the whole pipeline again per seed and reports the mean and the spread of the test macro F1, the
ROC-AUC and the false-positive rate. The published candidate is the first seed, so a sweep is reproducible.

## 7. Confidence intervals

The review asked for the intervals to be bootstrapped over **groups**, because emails from the same sender are
correlated.

- The false-positive rate: `fpr_with_ci()` in `backend/training/evaluate_modern.py` bootstraps over sender domains
  and reports the pooled rate, the domain-macro rate (the unweighted mean of the per-domain rates, so one dominant
  sender cannot hide behind a good pooled number) and a 95% interval for each.
- The recall: `recall_with_ci()` bootstraps over **campaigns**, for the same reason. Resampling messages would pretend
  that near-duplicate phishing are independent samples and would report an interval that is far too narrow.

## 8. The measurements

Every figure says which data it was measured on. The data it was measured on matters more than the number.

<!-- MEASUREMENT TABLE -->

## 9. What is NOT tested

These are the gaps, stated plainly so that nobody reads a number above as more than it is.

- **Other mail providers.** The legitimate mail is one inbox (Gmail, 2020-2026), SpamAssassin 2003 and CEAS 2008. A
  Microsoft 365 or a corporate Exchange mailbox is not represented at all, and the feature set knows the provider.
- **A second person's inbox.** The false-positive rate is measured on mail from the owner's own inbox, which is also
  part of the training data. `docs/18-open-manual-actions.md` item 2 is the request for a second inbox; until that
  arrives the rate is not transferable.
- **Non-English mail.** Every corpus is English.
- **Attachments-only phishing.** The feature set reads attachment metadata; a phishing message whose only payload is an
  attachment is not represented.
- **Real inbound email.** The evaluation uses files and webhooks, not a live mailbox provider.
- **A real campaign's full lifecycle.** The phishing corpora are collections of samples, not a live feed, so nothing
  here measures how the model behaves as a campaign unfolds.
- **Temporal drift beyond the corpus.** The training data ends in 2025 for the owner's mail and 2026 for Phishing Pot.
  Nothing measures how the model ages.
- **The LOW band is not safety.** Measured on the 2026 holdout, the model predicts 2.5% risk in the LOW band and the
  observed phishing rate there is 6.1%: 181 of 788 phishing messages land in LOW. The HIGH band is calibrated (predicted
  0.930, observed 0.949) and can be trusted. The UI must not present LOW as safe.

## 10. The commands

```powershell
# Fetch the corpora
cd backend
python -m training.download_datasets            # Nazario + SpamAssassin
python -m training.download_kaggle              # CEAS 2008, the 419 scams, SpamAssassin
python -m training.download_phishing_pot         # the modern phishing corpus

# Train, with the temporal split and a seed sweep
python -m training.train --source corpus \
  --phish-dir data/raw/nazario data/raw/phishing_pot \
  --legit-dir data/raw/spamassassin/easy_ham data/raw/spamassassin/hard_ham \
              data/raw/kaggle/ceas08/legitimate \
  --legit-mailbox data/raw/mailbox --legit-until 2026-01-01 \
  --split temporal --seeds 7,8,9 \
  --out models-eval --reports reports/modern

# Score the candidate on the 2026 holdout. This never writes a model.
python -m training.evaluate_modern --model-dir models-eval/<tag> \
  --mailbox data/raw/mailbox --since 2026-01-01 \
  --phish-dir data/raw/phishing_pot --out reports/modern

# The shortcut test
python -m scripts.source_leak_test --out ../.tmp/leak

# Privacy audit before anything is published
python -m scripts.audit_model --model models-eval/<tag> --mailbox data/raw/mailbox
```

Training without `--activate` writes a candidate and leaves the serving model alone.
