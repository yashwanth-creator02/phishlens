# Original PhishLens project definition (as provided by the team)

*Preserved from the first input of this work (before any design). Everything else in this repo builds on it.*

## Exact idea

**PhishLens is an Explainable AI-based phishing detection system that allows a user to forward a suspicious email to a
dedicated PhishLens bot email address and receive an understandable assessment of whether the message is potentially
phishing.** The purpose is not only to decide *whether* an email is suspicious, but to explain *what characteristics caused
the system to assign that risk*.

User experience: user receives an email -> uses the normal **Forward/Share** function -> sends it to the PhishLens bot
address -> PhishLens analyses it -> calculates phishing risk -> identifies the strongest reasons behind the prediction ->
shows risk level and reasons in the PhishLens web interface. The user never copies text, URLs, sender or headers into a form.

## What PhishLens analyses (six evidence categories)

1. **Sender and header information** - sender address/domain, relevant headers, consistency between header fields, whether
   the apparent sender and technical sending information agree.
2. **URLs** - suspicious structure, domain characteristics, mismatch between displayed link text and real destination,
   unusual domains, other URL indicators.
3. **Language, tone and urgency** - urgency, threats, pressure, unusual requests. *Poor grammar is NOT assumed to mean
   phishing*: wording is one category among several because modern phishing can be professionally written.
4. **Requested action** - click a link, provide credentials, verify an account, make/approve a payment, download a file,
   disclose sensitive information.
5. **Attachments** - presence, file type, suspicious characteristics.
6. **Unusual behaviour compared with previous messages** - compare the current message with earlier messages from the
   same sender where history exists ("this message differs substantially from the sender's previous messages").

## How detection works

Characteristics become measurable features (binary flags such as URL mismatch / urgency / attachment / header
inconsistency / new sender, plus numeric URL, domain and text measures). Features feed machine-learning models. The
project **studies existing approaches and develops/evaluates its own model**. Candidate models: **Logistic Regression**
(baseline), **Random Forest** (non-linear relations), **XGBoost** (advanced tree-based). Evaluation uses **F1-score,
ROC-AUC** and analysis of prediction errors. The final system uses the model selected by the evaluation.

**SHAP is not the detector.** The model first produces the prediction (e.g. probability 0.91); SHAP then estimates how
each feature contributed to that particular prediction. The system converts that into understandable statements, e.g.
*High Risk - 91%: the message contains a link whose visible text does not match the website it opens; the sender
information is inconsistent with the address used to deliver the message.*

## Risk output

Risk score + band **LOW / MEDIUM / HIGH**. Exact thresholds are determined during implementation/evaluation, not assumed.

## How the email reaches PhishLens

A dedicated bot address (e.g. `phishlens.bot@...`). The user forwards from Gmail/Outlook/any client. Ingestion technology
to investigate: **Gmail API / inbound email webhook** (exact mechanism to be finalised; the user interaction is fixed).

## Web interface

Presents: analysed email, sender information, risk score, Low/Medium/High level, important suspicious indicators,
plain-language explanations, extracted information, analysis history. It is the *presentation layer*; detection logic
does not live there.

## Browser add-on (future/advanced)

If time permits: a browser add-on to analyse a message inside webmail, reusing the **same** PhishLens detection
capability (not a separate detector). The primary system remains the email-forwarding workflow.

## Selected technology stack

| Layer | Choice |
|---|---|
| Frontend | React + TypeScript |
| Backend | Python + FastAPI |
| ML | Python + scikit-learn + XGBoost (compare Logistic Regression, Random Forest, XGBoost) |
| Explainable AI | SHAP |
| Explanation generation | **Rule/template-based initially**; no LLM in the core stack |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Email ingestion | Gmail API or inbound email webhook (to be finalised) |
| Processing | Synchronous initially; Redis + Celery later if needed |
| Deployment | Docker + a cloud/PaaS platform (provider not fixed) |

## One-flow summary

User receives email -> forwards to bot -> PhishLens receives it -> extracts email info -> extracts features -> ML model
analyses -> risk score -> Low/Medium/High -> SHAP identifies influential features -> converted to plain-language reasons
-> stored in Supabase -> shown in the web interface.

**Core idea:** build a phishing detection system that combines multiple observable phishing indicators with machine
learning and Explainable AI, then delivers the prediction **and its understandable reasons** through a convenient
email-forwarding workflow.
