# 16 - Demo script

A 7-8 minute walkthrough for the mini-project review. Every step names what the reviewer should see, so a failed
step is obvious instead of being narrated over.

## Before the session (do the day before, not in the room)

1. Backend: `.\backend.ps1` from the repository root. Wait for `Uvicorn running on http://0.0.0.0:8000`.
2. Frontend: `.\frontend.ps1`. Wait for `Local: http://localhost:5173`.
3. Check `http://localhost:8000/api/health` returns `"model_loaded": true`. If it is `false`, the model directory is
   empty: run `python -m training.train --source synthetic --n 2400 --out models --reports reports` inside
   `backend/` first.
4. Sign in once so the browser session is warm, then sign out, so the login step in the demo is real but fast.
5. Keep `backend/data/sample_emails/phish_paypal_direct.eml` on the desktop. Do not hunt for it during the demo.
6. Have `docs/screenshots/` open in a second window. If the live service dies mid-demo, switch to screenshots and
   say so plainly.

## Demo flow

| # | Step | What the reviewer sees | What to say |
|---|---|---|---|
| 1 | Open http://localhost:5173 | Analyst sign-in screen | "Nothing is readable without a session; analysis data is per-user." |
| 2 | Sign in with the seeded account | Dashboard: band counts and the five most recent analyses | "Every row is one analysed email, ordered newest first. The full archive is on the History screen." |
| 3 | Upload `phish_paypal_direct.eml` | New case at the top with a High band | "The score is 0-100; bands are Low <= 29, Medium 30-69, High >= 70." |
| 4 | Open the case | Band bar, plain-language reasons, evidence per reason, SHAP contribution table | "Reasons are not generated from the model alone: each one is checked against the parsed email before it is shown. No evidence, no reason." |
| 5 | Point at one reason | The quoted evidence (for example the mismatched link host) | "This is the difference from a black-box score: the claim and the evidence sit together." |
| 6 | Back to the dashboard, upload the legitimate newsletter sample | Low band | "Low risk does not hide the analysis; the score and features are still recorded." |
| 7 | History screen | Search, band filter, sort, pagination | "Built for a queue, not a single lookup." |
| 8 | Model screen | Active model identity, feature count, training metrics | "This model is fitted on real mail: Nazario phishing, SpamAssassin, and one modern inbox. It measured a 2.2% false-positive rate on 2,865 held-out legitimate messages, and it misses some phishing. The page shows the numbers and the caveats." |
| 9 | How it works screen | Six feature groups, pipeline stages | "65 features across header, URL, text, action, attachment, and behavioural groups; the same order at training and serving time." |
| 10 | Profile screen | Signed-in identity, forwarding alias, trusted-sender baseline upload, sign out | "The alias-based forwarding address, and the way to teach the system what a trusted sender looks like." |
| 11 | Status screen | API health, model loaded flag, last checked time | "Operational view: if the model failed to load, this page says it before a user trusts a score." |
| 12 | Delete the uploaded case, confirm the dialog | Row disappears; toast confirms | "Deletion is transactional and scoped to the owner; retention purges expired rows on a schedule." |

## Closing (30 seconds)

State the boundary explicitly: this is a working end-to-end prototype. The served model is fitted on real mail, but on
one person's inbox and a phishing corpus that is 20 years old, so the measured numbers describe that combination and
not phishing detection in general. Its recall misses the promotion gate it was measured against. A real inbound mail
provider and the user study are the next phase; the evaluation harness, the leakage guard and the grouped split are
already in the repository, so those numbers are reproducible rather than asserted.

## Fallbacks

- No network for Supabase sign-in: run with `AUTH_MODE=disabled` and no `VITE_SUPABASE_*` values, then skip step 1
  and start at the dashboard. Say that authentication is disabled for the local run.
- Backend not running: the upload fails with a visible error. Do not improvise a second instance mid-demo; switch to
  screenshots for the result pages and continue.
- Model missing: upload returns an error naming the missing model. Switch to the model page screenshot.

## Questions to expect

| Question | Answer |
|---|---|
| How accurate is it? | Measured on a held-out split: false-positive rate 0.018 at probability 0.5 and 0.021 at the LOW/MEDIUM boundary on 2,865 legitimate messages the model never saw, with phishing recall 0.770 on 788 held-out phishing messages. One inbox, one provider, one point in time, and a phishing corpus that ends in 2025: that is a floor, not a population estimate. The method is in `docs/21-modern-corpus-evaluation-plan.md`. |
| Why SHAP and not an LLM? | SHAP gives additive, auditable contributions per feature; the reason engine then checks the claim against the email. An LLM is used for none of the decisions. |
| What stops a wrong reason being shown? | Each reason has an evidence rule over the parsed email. A reason whose evidence fails is dropped, and Medium/High falls back to a generic statement. |
| What happens to forwarded mail? | Inline forwarding loses SPF/DKIM/DMARC; those are marked missing, not failed. Forward as attachment to keep the original headers. |
| Can two users see each other's cases? | The backend scopes every query by `user_id` and the PostgreSQL schema has Row-Level-Security as defence in depth. `backend/scripts/verify_rls.py` checks it in both directions when credentials are supplied. |
| What personal data is in the published model? | The model was fitted on one person's mailbox. `backend/scripts/audit_model.py` searches every file of the model directory for that mailbox's sender domains, email addresses and distinctive subject words, in plain text, UTF-16, gzip and base64, and reports zero findings; the SHAP background sample holds zero personal rows. The result is recorded in `backend/release/model/release.json`. |
