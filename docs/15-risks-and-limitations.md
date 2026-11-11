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
    [17](17-real-corpus-evaluation.md) and the teammate guide, step 7.
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
14. **No free, real, modern ham corpus exists.** The SpamAssassin public corpus ends in 2005; the public modern
    "spam/ham" sets that do exist are explicitly synthetic (generated mail with generated headers) and cannot serve as
    ground truth for real-world accuracy. This is why item 12 cannot be fixed by downloading something, and why the
    next step is a decision (see [21](21-modern-corpus-evaluation-plan.md) section 11) rather than more training.
15. **Phishing recall on 2024-2025 Nazario is in-sample.** The active model trained on those archives, so the 0.999
    recall measured on them is memorisation of campaigns it already saw. The clean window for that model is
    2015-2023. The harness now refuses to report a window the model was trained on unless it is told to.
16. **A model fitted on the owner's own mailbox is derived from private data.** It may be released only after
    `backend/scripts/audit_model.py` reports the artifact clean (no sender domain, no email address and no
    distinctive subject word from the mailbox in any file of the model directory) and only on the owner's explicit
    decision. The audit proves the artifact carries no personal data; it does not make the model accurate, and a
    model fitted on one inbox is fitted on one inbox.

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
