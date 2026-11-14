# 15 - Risks and limitations

## Known limitations of v0.1 (honest list)
1. **The demo model is trained on generated data.** The app's own output is not validated against real mail; real
   corpora are only used by the offline evaluation comparator (grouped-split F1 0.987 on 2003-2007 ham plus
   2003-2025 phishing, one split, no confidence interval - see [17](17-real-corpus-evaluation.md)).
2. **No real corpora are bundled.** You must download them (licences) with `training.download_datasets`, and their
   labels are corpus-of-origin rather than per-message adjudication.
3. **Behavioural features** need trusted history. The bot sees only what users send it, so history comes from "known-good" uploads and LOW-risk results. Real value likely needs a mailbox connector (future). Evaluation is semi-synthetic.
4. **Inline forwarding loses SPF/DKIM/DMARC.** Handled as *missing*; recommend "forward as attachment".
5. **Domain age** is not fetched (no WHOIS/RDAP yet) -> features are "missing" at serving time; the model was trained with ~50% availability to cope.
6. English-language text lexicons; no image/QR analysis; no HTML rendering analysis (e.g. hidden text).
7. SHAP explains the model, not reality: a reason can be true but unimportant, or a real signal can be absent from the list; hence verification + generic fallback + user study.
8. Calibration and selection share the validation split (optimistic); use nested CV for final numbers.
9. Postgres/Supabase, Docker and a real inbound provider were **not tested** in the build environment.
10. Security hardening list in [11](11-security-privacy.md) is not complete (encryption at rest, rate limits, signature verification).
11. **Authentication headers separate the corpora.** SpamAssassin's 2003 ham has no `Authentication-Results`, so
    `auth_missing` is near-constant for the legitimate class while Nazario phishing usually has passing headers;
    `from_returnpath_mismatch` is likewise inverted (84% of ham mismatch vs 13% of phishing, because old ham is
    mailing-list traffic). A model trained on these corpora treats present-and-passing headers and matching
    return-paths as phishing signals, so it scores modern, fully-authenticated legitimate mail near 1.0.
    Retraining on a modern ham corpus with real headers is the remedy, not threshold tuning. Full detail in
    [17](17-real-corpus-evaluation.md) and [21](21-modern-corpus-evaluation-plan.md).
12. **Measured: the corpora-trained model flags 99.9% of modern legitimate mail.** On 2,216 received messages from a
    real Gmail inbox (2020-2026, 87% with links, 99.7% with SPF) the corpus model `xgboost-corpus-20261110-s7`
    returns FPR 0.999 at probability 0.5 and at the LOW/MEDIUM boundary: 2,202 HIGH, 12 MEDIUM, 2 LOW. Mean
    probability is 0.996. This is a measured result on one inbox, not a population estimate, but the effect is far
    too large to be sampling noise. The corpus model is therefore **not fit for modern mail and must not be promoted
    to the live demo**. Details, method and the ablation in [21](21-modern-corpus-evaluation-plan.md).
13. **Removing the era features does not fix it.** Retraining on pre-2015 phishing plus 2003 ham with the 7
    authentication features removed still gives FPR 0.97 on the same inbox; adding `from_returnpath_mismatch` and
    `http_only` to the mask does not help either. The era shift is broader than authentication: modern legitimate
    mail also differs in link count, link length, click-request language and capitalisation. The binding constraint
    is the **absence of modern legitimate mail in training**, not any single feature.
14. **Adding modern legitimate mail to training fixes the false-positive side and costs recall.** Four candidates were
    trained and scored on one shared 2026 holdout (2,865 legitimate messages never seen in training, 788 phishing
    messages from the 2024-2025 archives). The candidate with modern ham and no 2003 ham flags 0.8% of legitimate mail
    at probability 0.5, against 99.9% for the corpus-only model, but catches only 72% of held-out phishing. Adding
    2003 ham back restores recall to 0.810 and the false-positive rate to 2.2%, at the cost of a domain-macro rate of
    0.112 that misses its 0.10 gate. The full table is in
    [21](21-modern-corpus-evaluation-plan.md) section 14. **No candidate passes every gate**: recall and Brier fail for
    all four, so a published model is a trade, not a clean win.
14. **The Kaggle corpora trade 0.040 of recall for half the false positives.** The released model adds CEAS 2008 and the
    419 scams to the phishing side and the Kaggle ham to the legitimate side. It passes the domain-macro gate that the
    previous release missed, 0.068 against 0.10, and its historical grouped F1 rises from 0.948 to 0.966, but its
    phishing recall at the triage boundary falls from 0.810 to 0.770. The corpora are 2002-2008 material, so they add
    volume from the era the model already handles rather than modern campaigns, and the recall gap is a data-vintage
    problem that more of the same will not close. The table is in
    [21](21-modern-corpus-evaluation-plan.md) section 15.
15. **No free, real, modern ham corpus exists.** The SpamAssassin public corpus ends in 2005; the public modern
    "spam/ham" sets that do exist are explicitly synthetic (generated mail with generated headers) and cannot serve as
    ground truth for real-world accuracy. This is why item 12 cannot be fixed by downloading something, and why the
    next step is a decision (see [21](21-modern-corpus-evaluation-plan.md) section 11) rather than more training.
16. **Phishing recall on 2024-2025 Nazario is in-sample.** The active model trained on those archives, so the 0.999
    recall measured on them is memorisation of campaigns it already saw. The clean window for that model is
    2015-2023. The harness now refuses to report a window the model was trained on unless it is told to.
17. **A model fitted on the owner's own mailbox is derived from private data.** It may be released only after
    `backend/scripts/audit_model.py` reports the artifact clean (no sender domain, no email address and no
    distinctive subject word from the mailbox in any file of the model directory) and only on the owner's explicit
    decision. The audit proves the artifact carries no personal data; it does not make the model accurate, and a
    model fitted on one inbox is fitted on one inbox.
18. **The published model is fitted on one person's mail and on a phishing corpus that is 20 years old.** Whatever its
    measured numbers are, they describe that combination, not phishing detection in general. The honest way to present
    it is as a measured system with a stated domain of validity, not as a detector.
19. **The credential-phrase matcher is not negation-aware.** It reads "never reveal your OTP" as a credential request,
    because it matches substrings. It fires on 3.9% of real modern mail, and those messages still score LOW, so it is
    a nuisance today. A negation-aware match would fix it, and the fix would need a retrain.
20. **The feature set identifies the mail provider and the era, not only the message.** A classifier trained to
    predict the corpus of *legitimate* mail alone separates three corpora with 0.981 accuracy, and 0.980 using only
    the 13 header and format features - `received_hops`, `from_returnpath_mismatch`, `auth_missing` and the
    SPF/DKIM/DMARC results carry it. The released model leans on those ten features for 10.1% of its gain, so the
    effect is bounded, but it is real. **The consequence for reporting: the 0.018 false-positive rate describes
    held-out 2026 mail from the owner's own inbox, and must not be quoted as a general false-positive rate.** The
    measurement, the gain shares and the reproduction steps are in
    [21](21-modern-corpus-evaluation-plan.md) section 17.
21. **The shortcut cannot be patched out feature by feature.** Removing one feature at a time changes the
    corpus-recovery accuracy by at most 0.010, because several features each identify the corpus on their own.
    Removing the whole 13-feature header group still leaves it at 0.885, and the format-only fingerprint (which
    header names are present, the shape of the Date and the Message-ID, the charset, the MIME structure, the line
    endings, the length of the Received chain) reaches 0.999 and survives dropping the MIME block and the transport
    headers. **The consequence: no feature engineering fixes this. The fix is training data from one world and a
    second inbox to measure on.** With five corpora the recovery accuracy is 0.976, and the candidate's own
    feature-group ablation agrees: dropping the header group costs it more than any other block. Reproduce with
    `python -m scripts.source_leak_test`; the method is in
    [22](22-training-methodology-and-measurements.md).
22. **More phishing data made the model worse, not better.** A candidate trained with the modern Phishing Pot corpus
    alongside the same legitimate corpora scores **0.129** false positives on the 2,865 held-out legitimate messages
    from 2026, against the released model's **0.018**, and its domain-macro rate is **0.472**. Two causes: its
    training set held the 2008 corpus only as legitimate mail, so the model scores that corpus's phishing as safe
    (recall 0.000 on 20,830 messages); and a temporal split over corpora from different eras separates the eras
    rather than sampling across them, leaving the fit partition 22% phishing. **The consequence: the honest way to
    add phishing data is with matched legitimate data from the same era, and the way to check it is the false-positive
    rate on the same holdout, not the training-set accuracy.**

## Project risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Real data performs far below targets | medium | high | report honestly; error analysis; stronger features; cross-dataset framing; keep explainability as the contribution |
| Public corpora are old/biased (Nazario, Enron) | high | medium | LLM-augmented tests, temporal split, state limits |
| Inbound email setup takes long | medium | medium | upload path already works; webhook simulated; start with one provider |
| Explanations mislead users | medium | high | verification rules, generic fallback, audit, user study |
| User study recruitment / ethics delays | medium | medium | start early; pilot; small but well-run study |
| Time (16 weeks, 4 students) | high | medium | scope cut order: browser add-on -> Gmail API -> LLM wording -> async queue |
| Sender-history poisoning or leakage | low | medium | update only from safe mail (done); "mark as safe" UI |
| Dependency drift (SHAP/XGBoost versions) | low | medium | `requirements.lock.txt`, CI |
| The feature set identifies the mail provider and the era, not just the message | high | high | measured: legitimate mail from three corpora is classified by source with 0.981 accuracy (0.980 on header features alone). The released model leans on those features for 10.1% of its gain, so the effect is bounded but real. **Consequence: the 0.018 false-positive rate describes held-out mail from the owner's own inbox and must not be quoted as a general FPR.** Detail and reproduction in [21](21-modern-corpus-evaluation-plan.md) section 17 |
