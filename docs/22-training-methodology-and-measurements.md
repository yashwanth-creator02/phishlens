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

## 8. Are the reasons faithful?

A reason is a sentence about the email. It is only worth reading if the features it names are what moved the
score. `backend/app/explain/faithfulness.py` measures that, and `backend/tests/test_faithfulness.py` checks it
against the model that ships.

**The deletion test.** The features the reasons cite are replaced with the model's own reference values (the mean
of its background sample, not zero, because for a feature where most mail is 1, zero is not a neutral value) and
the message is scored again. Deleting features always moves a score a little, so the only question that matters is
whether the cited features move it **more than a random set of the same size**. On the invoice sample the cited
features account for **0.107** of the raw score, against a random mean of **0.012** and a random worst case of
**0.049**: the reasons name the features that matter, and by a margin that chance does not explain.

**The test knows when it cannot say anything.** On the PayPal sample the released model is saturated (raw
probability 0.99999), so no feature set moves the score: deleting the cited features changes it by 0.0004 and the
best random set changes it by 0.0017. The check reports `has_power: false` there instead of a pass, because a
number that cannot distinguish the reasons from chance must not be read as a verdict. The consequence is worth
stating: **the HIGH band has no score resolution, so its explanations can only be trusted through their SHAP
contribution, not through their effect on the score.**

**Stability.** The same message, reformatted without changing its meaning, must get the same verdict. A blank line
in the body and the headers in another order change no feature at all, so the band, the score and the reasons come
out identical for every sample. Scoring the same message twice gives the same answer as well.

One thing this ruled out: adding noise to the feature vector is **not** a stability test. A binary flag moved from
1 to 1.01 crosses the model's split and means the opposite of what it meant, so a legitimate message's score jumped
from 0.10 to 0.98. The perturbation has to be one that leaves the message meaning the same thing.

## 9. The measurements

Every figure says which data it was measured on. The data it was measured on matters more than the number.

| metric | data it was measured on | threshold | value | 95% interval |
|---|---|---|---|---|
| false-positive rate | 2,865 legitimate messages from one inbox, dated 2026 | p >= 0.50 | 0.018 | - |
| false-positive rate, same set | same | band boundary 0.29 | 0.021 | 0.009 - 0.044 |
| domain-macro false-positive rate | same, per sender domain | band boundary | 0.068 | 0.034 - 0.108 |
| phishing recall | 788 phishing messages, Nazario 2024-2025 | p >= 0.50 | 0.754 | - |
| phishing recall, same set | same | band boundary 0.29 | 0.770 | - |
| combined F1 | both sets together | p >= 0.50 | 0.829 | - |
| ROC-AUC | both sets together | - | 0.967 | - |
| PR-AUC | both sets together | - | 0.906 | - |
| Brier score | the training holdout | - | 0.026 | - |
| recall at a 1% false-positive rate | both sets together | p >= 0.722 | 0.662 | - |
| recall at a 5% false-positive rate | both sets together | p >= 0.203 | 0.806 | - |
| LOW band, observed phishing rate | 788 phishing messages | score <= 29 | 0.061 | - |
| MEDIUM band, observed phishing rate | same | 30 - 69 | 0.730 | - |
| HIGH band, observed phishing rate | same | score >= 70 | 0.949 | - |
| macro F1, candidate with the temporal split | 5,392 messages: 5,156 modern phishing and 236 legitimate, held out by date and campaign | p >= 0.50 | 0.824 | seed spread 0.819 +/- 0.009 |
| recall, same candidate | the 5,156 modern phishing | p >= 0.50 | 0.959 | - |
| ROC-AUC, same candidate | the 5,392 | - | 0.985 | seed spread 0.984 +/- 0.002 |
| **false-positive rate, the candidate** | **the same 2,865 legitimate messages** | p >= 0.50 | **0.129** | 0.125 - 0.422 |
| **false-positive rate, the candidate** | same | band boundary 0.29 | **0.234** | - |
| **domain-macro false-positive rate, the candidate** | same, per sender domain | band boundary | **0.472** | - |
| **phishing recall, the candidate** | 20,830 messages of 2008-era phishing | p >= 0.50 | **0.000** | - |
| corpus recovery, legitimate mail only | 4,500 messages from three corpora | - | 0.981 | chance is 0.333 |
| corpus recovery, header features only | the same | - | 0.980 | - |
| corpus recovery, format features only | the same | - | 0.999 | - |
| corpus recovery after removing the header group | the same | - | 0.885 | the leak survives |
| deletion test, cited features | the invoice sample, raw score | - | 0.107 | random worst case 0.049 |

The first block is the released model. The second is the candidate, and the last four rows are why the candidate was
**not** promoted. On the very same 2,865 legitimate messages its false-positive rate is 0.129 against the released
model's 0.018, and its domain-macro rate is 0.472: nearly half of the legitimate mail is flagged. It also does not
recognise 2008-era phishing at all (recall 0.000 on 20,830 messages).

Part of that second failure is the candidate's own corpus composition, and the reason is worth stating because it is
a trap: its training set contained the 2008 corpus **only as legitimate mail**, so the model learned that mail from
that corpus is safe. Part of the first failure is the method: a temporal split over corpora from different eras does
not sample randomly across time, it separates the eras, so the fit partition ends up 22% phishing and the model
learns the era rather than the message. Adding a modern phishing corpus without a matched modern legitimate corpus
made the era shortcut worse, not better.

Reproduce each row with the commands in section 11; the reports are written to `backend/reports/`.

## 10. What is NOT tested

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

## 11. The commands

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
python -m training.evaluate_modern --model models-eval/<tag> \
  --mailbox data/raw/mailbox --mailbox-since 2026-01-01 \
  --phish-dir data/raw/kaggle/ceas08/phishing \
  --phish-since 2000-01-01 --phish-until 2024-01-01 \
  --out reports/modern-candidate

# The shortcut test
python -m scripts.source_leak_test --out ../.tmp/leak

# Privacy audit before anything is published
python -m scripts.audit_model --model models-eval/<tag> --mailbox data/raw/mailbox
```

Training without `--activate` writes a candidate and leaves the serving model alone.
