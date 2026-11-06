# 15 - Risks and limitations

## Known limitations of v0.1 (honest list)
1. **The demo model is trained on generated data.** The app's own output is not validated against real mail; real
   corpora are only used by the offline evaluation comparator (grouped-split F1 0.948 on 2003-2007 data, one split,
   no confidence interval - see [17](17-real-corpus-evaluation.md)).
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
