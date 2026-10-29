import copy
from pptx import Presentation

prs = Presentation('/home/claude/work/ppt/deck.pptx')
S = lambda n: prs.slides[n - 1]

def shape(sl, name):
    for sh in sl.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)

def setp(n, name, pi, *texts):
    """Replace run texts of paragraph pi in shape `name` on slide n (run count must match)."""
    sh = shape(S(n), name)
    para = sh.text_frame.paragraphs[pi]
    runs = para.runs
    assert len(runs) == len(texts), (n, name, pi, len(runs), len(texts))
    for r, t in zip(runs, texts):
        r.text = t

def dup_para(n, name, pi):
    sh = shape(S(n), name)
    p = sh.text_frame.paragraphs[pi]._p
    new = copy.deepcopy(p)
    p.addnext(new)

def setc(n, name, r, c, pi, text):
    sh = shape(S(n), name)
    cell = sh.table.cell(r, c)
    runs = cell.text_frame.paragraphs[pi].runs
    assert len(runs) == 1, (n, r, c, pi, len(runs))
    runs[0].text = text

# ------------------------------------------------------------------ slide 1
setp(1, 'Subtitle 2', 0, 'PhishLens: An Explainable AI System')
setp(1, 'Subtitle 2', 1, 'for Phishing Detection and Risk Justification')
setp(1, 'Subtitle 2', 2, 'Forward a suspicious email  +  get a risk level with plain-language reasons (SHAP-based XAI)')
setp(1, 'Subtitle 2', 3, 'Presented by  (', 'Batch 45)')
dup_para(1, 'Subtitle 2', 4)
setp(1, 'Subtitle 2', 4, 'Md Saquib Ali (1TE24CS174)   |   N Sai Yashwanth Simha (1TE24CS178)')
setp(1, 'Subtitle 2', 5, 'Nakshatra Chaudhary (1TE24CS179)   |   Mourya M Goankar (1BY24CS173)')
setp(1, 'Subtitle 2', 7, 'Dr. Shanthi D L')

# ------------------------------------------------------------------ slide 3 Introduction
t = 'TextBox 6'
setp(3, t, 0, 'Phishing tricks people, not software, and it keeps growing.')
setp(3, t, 1, 'APWG logged about 1.07 million attacks in Q2 2026 [13]; phishing was also the most reported US cybercrime in 2025 [14].')
setp(3, t, 2, 'Filters mark a message as unsafe but give no reason, so users ignore the warning or stop trusting it.')
setp(3, t, 3, 'Generative AI now writes fluent phishing, so poor grammar is no longer a reliable clue [6], [7].')
setp(3, t, 4, 'Reported results: ', 'AI-written spear phishing got a 54% click rate, equal to human experts [6]; explainable nudges raised user detection accuracy by 10.1% [9].')
setp(3, t, 5, 'PhishLens: ', 'forward a suspicious email to a bot address and get a Low / Medium / High risk level with plain-language reasons from SHAP [8], shown in a web interface.')

# ------------------------------------------------------------------ slide 4 Problem statement
setp(4, 'TextBox 6', 0, 'Phishing detectors say that a message looks unsafe but not why. Users cannot judge such a warning, and detectors that rely on one kind of clue (links or wording) are easier to fool, especially now that AI writes the emails.')
t = 'TextBox 7'
setp(4, t, 0, 'No reasons given: ', 'a bare "suspicious" banner gives the reader nothing to check.')
setp(4, t, 1, 'Narrow evidence: ', 'many detectors use only URLs or only text [1], [4].')
setp(4, t, 2, 'Weak generalisation: ', 'accuracy is often reported on a single dataset [1].')
setp(4, t, 3, 'AI-written phishing: ', 'fluent text weakens wording-based detection [6], [7].')
setp(4, t, 4, 'Context ignored: ', "a sender's earlier behaviour is rarely used [12].")
setp(4, t, 5, 'Unproven benefit: ', 'few systems test whether explanations help users [11].')

# ------------------------------------------------------------------ slide 5 Objectives
t = 'TextBox 7'
setp(5, t, 0, '1. To Build a Multi-Signal Phishing Dataset and Feature Set')
setp(5, t, 1, 'Collect phishing and genuine messages from public datasets, supplement them with representative samples, and define measurable features across six clue categories (sender and headers, URLs, language and urgency, requested action, attachments, and unusual behaviour compared with earlier messages from the same sender), documenting each feature\'s meaning and extraction rule.')
setp(5, t, 2, '2. Evaluate Existing Models and Develop Our Own')
setp(5, t, 3, 'Study and evaluate an existing phishing detection model, develop our own machine learning model (Logistic Regression, Random Forest, XGBoost), compare them using F1-score, ROC-AUC and error analysis, and select the most suitable approach for the proposed system.')
setp(5, t, 4, '3. Explain Every Prediction in Plain Language')
setp(5, t, 5, 'Integrate SHapley Additive exPlanations (SHAP) with the selected model to find the features that influence each prediction, and convert these technical contributions into clear statements, such as "the link text does not match the website it opens", each checked against evidence in the email.')
setp(5, t, 6, '4. Deliver the Analysis Through an Email-Forwarding Workflow and Web Interface')
setp(5, t, 7, 'Provide a dedicated bot email address so that users can forward a received email, then show the risk level (Low, Medium or High) and the supporting reasons in a web interface; test the system for accuracy and study every kind of mistake it makes.')
setp(5, t, 8, '5. Evaluate the Value of the Explanations and Extend to the Browser')
setp(5, t, 9, 'Run a user study to check whether the explanations improve users\' ability to identify phishing messages and, as an advanced goal, develop a browser add-on that analyses messages directly inside a webmail interface.')
setp(5, 'TextBox 2', 0, 'BMSIT&M, Dept. of CSE  |  Mini Project - Review 1')
setp(5, 'TextBox 3', 0, '5')

# ------------------------------------------------------------------ slide 6 Literature (1/3)
T6 = 'Table 6'
rows = [
 ('[1] Yi et al., Security and Privacy 2026', 'Phishing URL detection and interpretability with ML: a cross-dataset approach',
  'Random Forest, XGBoost and LightGBM on 87 URL features; trained on 11,430 URLs and tested on four sets; SHAP for interpretation; Flask web tool.',
  'Average accuracy above 94% on four test sets; Random Forest generalised best (~2.90% average error); google_index and page_rank were top SHAP features.',
  'URL and page features only; SHAP shown as analyst plots, not user-readable reasons; no email headers or attachments; no user study.'),
 ('[2] Uddin et al., J. Engineering 2025', 'Explainable ML for phishing site detection using boosting models and SHAP',
  'Gradient boosting, XGBoost and LightGBM with SHAP on a public Kaggle phishing-website dataset.',
  'XGBoost reached 97.78% accuracy; SHAP plots show each feature\'s contribution to the classifiers.',
  'Website features, not emails; single public dataset; no plain-language output and no forwarding workflow.'),
 ('[3] Bhavana et al., IEEE IC3 2025', 'Context-aware phishing email detection using hybrid ML and explainable AI',
  'RF, Naive Bayes, XGBoost, CNN, LSTM, CNN-LSTM and DistilBERT on a corpus merged from three public datasets; LIME, SHAP and BERTViz for interpretation.',
  'Reports a scalable, interpretable pipeline for real-time phishing email detection (as stated in the abstract).',
  'Interpretation is at model level; user-facing delivery and a user evaluation are not reported in the abstract.'),
 ('[4] Altwaijry et al., Sensors 2024', 'Advancing phishing email detection: a comparative study of deep learning models',
  'Compares several deep-learning models (including a CNN) for phishing email detection.',
  'CNN reached 99.68% accuracy on about 6,400 emails (as tabulated in [1]).',
  'Single dataset; no cross-dataset test; no explanation of individual decisions.'),
]
for i, (a, b, c, d, e) in enumerate(rows, start=1):
    setc(6, T6, i, 0, 0, a); setc(6, T6, i, 0, 1, b)
    setc(6, T6, i, 1, 0, c); setc(6, T6, i, 2, 0, d); setc(6, T6, i, 3, 0, e)

# ------------------------------------------------------------------ slide 7 Literature (2/3)
T7 = 'Table 6'
rows = [
 ('[5] Prabakaran et al., IET Inf. Security 2023', 'Deep learning-based phishing detection using variational autoencoders',
  'Deep-learning mechanism that uses variational autoencoders to identify malicious URLs.',
  'The authors report an enhanced mechanism that effectively identifies malicious URLs.',
  'URL evidence only; no per-message explanation for the user.'),
 ('[6] Heiding et al., Expert Syst. Appl. 2026', "Evaluating LLMs' ability to automate spear phishing",
  'Human-subject study (N = 101): control, human-expert, AI-automated and AI + human emails; LLMs also tested as detectors on 381 emails.',
  'Click rates 12% (control), 54% (expert), 54% (AI), 56% (AI + human); Claude 3.5 Sonnet detected 97.25% with no false positives.',
  'Shows wording is unreliable, but gives no explainable, multi-signal detector for ordinary users.'),
 ('[7] Afane et al., IEEE BigData 2024', 'Next-generation phishing: how LLM agents empower cyber attackers',
  'Tests Gmail filter, SpamAssassin, Proofpoint and ML models on LLM-rephrased phishing; builds the LLM-Nazario dataset.',
  'Detection effectiveness dropped on LLM-rephrased emails; LLM-based augmentation proposed for training.',
  'Evaluates and augments but does not explain verdicts to users; no sender-context features.'),
 ('[8] Lundberg & Lee, NeurIPS 2017', 'A unified approach to interpreting model predictions',
  'SHAP: Shapley-value feature attribution that unifies several earlier explanation methods.',
  'Local feature contributions that add up to the model output, with desirable consistency properties.',
  'General method, not phishing-specific; outputs numbers, so a text layer is needed for end users.'),
]
for i, (a, b, c, d, e) in enumerate(rows, start=0):
    r = i  # slide 7 table has no header row; data rows start at 0
    setc(7, T7, r, 0, 0, a); setc(7, T7, r, 0, 1, b)
    setc(7, T7, r, 1, 0, c); setc(7, T7, r, 2, 0, d); setc(7, T7, r, 3, 0, e)

# ------------------------------------------------------------------ slide 8 Literature (3/3)
T8 = 'Table 6'
rows = [
 ('[9] Wagner et al., WISP 2025', 'Email phishing prevention: an explainable nudging approach',
  'Between-subjects experiment comparing an XAI-enabled nudge, a popular existing nudge and no nudge.',
  'The XAI nudge improved detection accuracy by 10.1% and reduced cognitive load.',
  'Studies the nudge, not an end-to-end detector with ingestion, scoring and sender history.'),
 ('[10] Roy et al., arXiv 2025', '"Explain, Don\'t Just Warn!": real-time phishing warnings with contextual cues',
  'LLaMA-based explainable warnings with annotated screenshots for flagged websites; 150-participant user study.',
  'Better understanding of phishing indicators and higher accuracy, most for low-proficiency users; released as a browser extension.',
  'Web pages, not forwarded emails; LLM-generated text can hallucinate [11].'),
 ('[11] Cau et al., arXiv 2025', 'Can LLMs automate phishing warning explanations?',
  'Between-subjects study (N = 750): manual vs Claude 3.5 Sonnet vs Llama 3.3 explanations, feature-based and counterfactual.',
  'LLM explanations protected users about as well as expert-written ones; feature-based suited true phishing, counterfactual cut false-positive clicks.',
  'Advises deterministic checks against hallucination; no detector pipeline.'),
 ('[12] Ho et al., USENIX Security 2019', 'Detecting and characterizing lateral phishing at scale',
  'Studies lateral phishing from compromised accounts; the detector uses historical communication behaviour.',
  "Shows that behaviour relative to a sender's history can expose attacks that content alone misses.",
  'Enterprise setting; no explanation to the user and no forward-to-bot workflow.'),
]
for i, (a, b, c, d, e) in enumerate(rows, start=1):
    setc(8, T8, i, 0, 0, a); setc(8, T8, i, 0, 1, b)
    setc(8, T8, i, 1, 0, c); setc(8, T8, i, 2, 0, d); setc(8, T8, i, 3, 0, e)

# ------------------------------------------------------------------ slide 9 Gap analysis
T9 = 'Table 6'
setc(9, T9, 0, 5, 0, 'PhishLens')
grid = [
 ('SHAP / LIME explanations',   ['Yes (SHAP)', 'Yes (SHAP)', 'Yes (LIME, SHAP)', 'No', 'Yes (SHAP)']),
 ('Plain-language reasons',     ['No', 'No', 'Not reported', 'No', 'Yes']),
 ('Several evidence groups',    ['URL + page', 'Site features', 'Not stated', 'Not stated', 'Six groups']),
 ('Sender-history features',    ['No', 'No', 'Not stated', 'No', 'Yes']),
 ('Cross-dataset testing',      ['Yes', 'No', 'Merged sets', 'No', 'Yes (planned)']),
 ('Forward-to-bot workflow',    ['No', 'No', 'No', 'No', 'Yes']),
]
for r, (cap, vals) in enumerate(grid, start=1):
    setc(9, T9, r, 0, 0, cap)
    for c, v in enumerate(vals, start=1):
        setc(9, T9, r, c, 0, v)
setp(9, 'TextBox 7', 0, 'Each paper solves only part of the problem. Among the surveyed papers, none combines several evidence groups, sender history and plain-language reasons in a forward-and-explain workflow.')

# ------------------------------------------------------------------ slide 10 Existing system
setp(10, 'Rectangle 6', 0, 'Attacker')
setp(10, 'Rectangle 8', 0, 'Mail server')
setp(10, 'Rectangle 10', 0, 'Spam / phishing')
setp(10, 'Rectangle 10', 1, 'filter')
setp(10, 'Rectangle 12', 0, 'Warning')
setp(10, 'Rectangle 12', 1, 'banner')
setp(10, 'Rectangle 14', 0, 'User decides')
t = 'TextBox 15'
setp(10, t, 0, 'Typical email filters')
setp(10, t, 1, 'Verdict only: "suspicious", with no reason')
setp(10, t, 2, 'One kind of clue: URLs or text alone')
setp(10, t, 3, 'Wording checks weakened by AI-written mail')
setp(10, t, 4, 'User must paste or install tools to ask')
t = 'TextBox 16'
setp(10, t, 0, 'Existing explainable research')
setp(10, t, 1, 'SHAP / LIME plots meant for analysts [1], [2], [3]')
setp(10, t, 2, 'Mostly one dataset; few cross-dataset tests [1]')
setp(10, t, 3, 'User studies exist, but for warnings and websites [9], [10]')
setp(10, t, 4, 'No forward-to-bot workflow with sender history')

# ------------------------------------------------------------------ slide 11 Proposed system
setp(11, 'TextBox 6', 0, 'Forward, analyse, explain: every score comes with reasons.')
t = 'TextBox 7'
setp(11, t, 0, 'Detection layer (FastAPI + ML)')
setp(11, t, 1, 'Email ingestion: bot address, MIME parser')
setp(11, t, 2, 'Six clue groups as ML features')
setp(11, t, 3, 'LR, Random Forest and XGBoost compared')
setp(11, t, 4, 'Risk score 0-100: Low / Medium / High')
setp(11, t, 5, "Sender history for unusual-behaviour checks")
t = 'TextBox 8'
setp(11, t, 0, 'Explanation and delivery (SHAP + React)')
setp(11, t, 1, 'SHAP finds the top contributing features')
setp(11, t, 2, 'Templates turn features into plain sentences')
setp(11, t, 3, 'Each reason is checked against the email')
setp(11, t, 4, 'Results stored in Supabase, shown in web UI')
setp(11, t, 5, 'Browser add-on as a stretch goal')

# ------------------------------------------------------------------ slide 12 Methodology
setp(12, 'TextBox 7', 0, 'Phase A: build and select the model (offline)')
for nm, tx in [('Rectangle 8', 'Collect datasets'), ('Rectangle 10', 'Clean and label'), ('Rectangle 12', 'Extract features'),
               ('Rectangle 14', 'Train and compare'), ('Rectangle 16', 'Select and calibrate')]:
    setp(12, nm, 0, tx)
setp(12, 'TextBox 18', 0, 'Phase B: analyse a forwarded email (live)')
for nm, tx in [('Rectangle 19', 'Forward to bot address'), ('Rectangle 21', 'Parse and extract features'),
               ('Rectangle 23', 'Score and SHAP reasons'), ('Rectangle 25', 'Show risk and reasons')]:
    setp(12, nm, 0, tx)
setp(12, 'TextBox 27', 0, 'Same code in both phases: ', 'the feature-extraction code used for training also runs on live emails, so the model sees identical features. Each result is stored with its model version.')
setp(12, 'TextBox 27', 1, 'Example: ', 'model output 0.91 gives risk score 91% (High); top SHAP features: link mismatch, header inconsistency, urgency (illustrative).')

# ------------------------------------------------------------------ slide 13 Module design
t = 'TextBox 6'
setp(13, t, 0, 'Feature extraction engine')
setp(13, t, 1, 'Header: ', 'SPF / DKIM / DMARC results; From, Reply-To and Return-Path consistency.')
setp(13, t, 2, 'URL: ', 'link text vs real destination, IP hosts, shorteners, domain age.')
setp(13, t, 3, 'Text and action: ', 'urgency and threat language; asks for login, payment or download.')
setp(13, t, 4, 'Files and history: ', "risky attachment types; deviation from the sender's past messages.")
setp(13, 'TextBox 7', 0, 'EMAIL → PARSE → 6 FEATURE MODULES → ONE VECTOR')
t = 'TextBox 8'
setp(13, t, 0, 'Model, explanation and scoring engine')
setp(13, t, 1, 'Models: ', 'Logistic Regression baseline, Random Forest, XGBoost; compared on F1 and ROC-AUC.')
setp(13, t, 2, 'SHAP [8]: ', "each feature's contribution to one prediction (exact for tree models).")
setp(13, t, 3, 'Reasons: ', 'top risk-raising features are checked, then filled into sentence templates.')
setp(13, t, 4, 'Risk band: ', 'calibrated probability to 0-100 score to Low / Medium / High.')
setp(13, 'TextBox 9', 0, 'VECTOR → MODEL → SHAP → REASONS → RISK BAND')

# ------------------------------------------------------------------ slide 14 Architecture
setp(14, 'Rectangle 6', 0, 'Client: web app (React + TypeScript)  |  User forwards the email from Gmail / Outlook to the bot address')
setp(14, 'TextBox 10', 0, 'Phase A: ingest and extract')
setp(14, 'TextBox 12', 0, 'Phase B: score and explain')
setp(14, 'TextBox 14', 0, 'Feature vector')
pairs = {
 'Rectangle 15': ('Ingestion', 'bot address, webhook'),
 'Rectangle 18': ('Supabase', 'raw emails, users'),
 'Rectangle 19': ('Parser', 'headers, text, links'),
 'Rectangle 22': ('Python email lib', 'MIME to fields, files'),
 'Rectangle 23': ('Features', 'six evidence groups'),
 'Rectangle 25': ('Sender history', 'profile per sender'),
 'Rectangle 26': ('ML model', 'LR, RF, XGBoost'),
 'Rectangle 29': ('Supabase DB', 'analyses, reasons'),
 'Rectangle 30': ('SHAP', 'feature contributions'),
 'Rectangle 33': ('Templates', 'feature to sentence'),
 'Rectangle 34': ('Risk scorer', 'score, Low / Med / High'),
 'Rectangle 36': ('Web UI', 'score, band, reasons'),
}
for nm, (a, b) in pairs.items():
    setp(14, nm, 0, a); setp(14, nm, 1, b)
setp(14, 'TextBox 37', 0, 'No black-box verdicts: every reason shown comes from a SHAP-ranked feature and is checked against evidence extracted from the email.')

# ------------------------------------------------------------------ slide 15 Tools
T15 = 'Table 6'
tools = [
 ('Frontend', 'React, TypeScript, Supabase Auth client'),
 ('Backend', 'Python, FastAPI, Uvicorn'),
 ('Database', 'Supabase PostgreSQL (Auth, Storage)'),
 ('Machine learning', 'scikit-learn, XGBoost, pandas, NumPy'),
 ('Explainability', 'SHAP, rule and template engine'),
 ('Email ingestion', 'Inbound email webhook or Gmail API'),
 ('Evaluation', 'F1-score, ROC-AUC, PR-AUC, confusion matrices'),
 ('Dev & testing', 'Git/GitHub, Docker, pytest, Postman'),
]
for i, (a, b) in enumerate(tools, start=1):
    setc(15, T15, i, 0, 0, a); setc(15, T15, i, 1, 0, b)

# ------------------------------------------------------------------ slide 16 SRS
t = 'TextBox 6'
for i, tx in enumerate(['User registration and login (Supabase Auth)', 'Receive forwarded email at the bot address',
                        'Extract features from six evidence groups', 'Risk score with Low / Medium / High band',
                        'SHAP-based plain-language reasons', 'Analysis history in the web interface'], start=1):
    setp(16, t, i, tx)
t = 'TextBox 7'
for i, tx in enumerate(['Security: signed webhooks, encrypted raw email, per-user access rules',
                        'Reliability: same feature code for training and serving',
                        'Transparency: each reason traceable to a feature',
                        'Usability: no forms, just forward the email'], start=1):
    setp(16, t, i, tx)
t = 'TextBox 8'
for i, tx in enumerate(['Laptop with 8 GB+ RAM (CPU is enough)', 'Windows / Linux / macOS', 'Python, Node.js, Docker',
                        'Modern web browser', 'Internet for Supabase and email provider'], start=1):
    setp(16, t, i, tx)

# ------------------------------------------------------------------ slide 17 Outcome
t = 'TextBox 6'
for i, tx in enumerate(['Working prototype: forward an email, get a risk level and reasons.',
                        'Six evidence groups feed every prediction.',
                        'Existing model vs our model compared on F1 and ROC-AUC.',
                        'SHAP reasons shown in plain language, with evidence.',
                        'User study shows whether reasons help users spot phishing.']):
    setp(17, t, i, tx)
T17 = 'Table 7'
out = [('Feature extraction, models, SHAP', 'Real'), ('Training data', 'Public sets + samples'),
       ('Bot-address email ingestion', 'Real (test mailbox)'), ('Risk bands and reasons', 'Real'),
       ('Sender history', 'Semi-synthetic test'), ('Browser add-on', 'Stretch goal')]
for i, (a, b) in enumerate(out, start=1):
    setc(17, T17, i, 0, 0, a); setc(17, T17, i, 1, 0, b)
setp(17, 'TextBox 8', 0, 'Targets to be validated: macro F1 of 0.95 or more, low false-positive rate.')

# ------------------------------------------------------------------ slide 18 Applications
t = 'TextBox 6'
setp(18, t, 0, 'Everyday users: ', 'check a doubtful email by forwarding it, and learn from the reasons.')
setp(18, t, 1, 'Students and new internet users: ', 'see what phishing clues look like in real messages.')
setp(18, t, 2, 'Small businesses: ', 'a second opinion on invoices and payment requests.')
setp(18, t, 3, 'Security awareness training: ', 'real examples with explanations, not made-up ones.')
setp(18, t, 4, 'Helpdesks and IT teams: ', 'faster triage of reported emails.')
setp(18, t, 5, 'Researchers: ', 'documented features and evaluation method to build upon.')

# ------------------------------------------------------------------ slide 19 SDGs
t = 'TextBox 6'
setp(19, t, 0, 'SDG 9, Industry, Innovation and Infrastructure (Target 9.1): ', 'protects digital communication, now part of reliable infrastructure.')
setp(19, t, 1, 'SDG 9 (Target 9.c): ', 'access to the internet is only worth having if it is safe; clear reasons help new users stay safe.')
setp(19, t, 2, 'SDG 9 (Target 9.5): ', 'an openly documented dataset, feature dictionary and test method for other researchers.')

# ------------------------------------------------------------------ slide 20 Conclusion
t = 'TextBox 6'
setp(20, t, 1, 'PhishLens aims to show that phishing detection can be accurate and understandable: a forwarded email is checked on six evidence groups, scored, and explained with SHAP-based reasons.')
setp(20, t, 2, 'It combines the multi-signal detection, explainability and user-study ideas of the surveyed papers in one forward-and-explain system, and states clearly what is tested and what is simulated.')
t = 'TextBox 7'
for i, tx in enumerate(['Browser add-on for webmail', 'Asynchronous processing (Redis + Celery)', 'Gmail API ingestion',
                        'Counterfactual and LLM-worded explanations', 'Image and QR-code phishing', 'Multilingual support'], start=1):
    setp(20, t, i, tx)

# ------------------------------------------------------------------ slides 21-22 References
refs = {
 21: [
  ('[1]  ', 'L. Yi, A. Omotosho and H. Balogun, “Phishing URL detection and interpretability with machine learning: A cross-dataset approach,” Security and Privacy, vol. 9, no. 1, Art. no. e70175, 2026, doi: 10.1002/spy2.70175.'),
  ('[2]  ', 'K. M. M. Uddin, N. Biswas, S. T. Rikta, M. Nur-A-Alam and R. Mostafiz, “Explainable machine learning for phishing site detection: A high-efficiency approach using boosting models and SHAP,” The Journal of Engineering, vol. 2025, no. 1, 2025, doi: 10.1049/tje2.70110.'),
  ('[3]  ', 'B. S. Bhavana, S. Srivastava, D. Ghosh, V. Kumar and P. Gupta, “Context-aware phishing email detection using hybrid machine learning and explainable AI,” in Proc. 17th Int. Conf. Contemporary Computing (IC3), Noida, India, 2025, pp. 1–6, doi: 10.1109/IC366947.2025.11290431.'),
  ('[4]  ', 'N. Altwaijry, I. Al-Turaiki, R. Alotaibi and F. Alakeel, “Advancing phishing email detection: A comparative study of deep learning models,” Sensors, vol. 24, no. 7, p. 2077, Mar. 2024.'),
  ('[5]  ', 'M. K. Prabakaran, P. Meenakshi Sundaram and A. D. Chandrasekar, “An enhanced deep learning-based phishing detection mechanism to effectively identify malicious URLs using variational autoencoders,” IET Information Security, vol. 17, no. 3, pp. 423–440, May 2023.'),
  ('[6]  ', 'F. Heiding, S. Lermen, A. Kao, C. M. Verdun, B. Schneier and A. Vishwanath, “Evaluating large language models’ ability to automate spear phishing,” Expert Systems with Applications, vol. 314, Art. no. 131546, 2026, doi: 10.1016/j.eswa.2026.131546.'),
 ],
 22: [
  ('[7]  ', 'K. Afane, W. Wei, Y. Mao, J. Farooq and J. Chen, “Next-generation phishing: How LLM agents empower cyber attackers,” in Proc. IEEE Int. Conf. Big Data (BigData), Dec. 2024, doi: 10.1109/BigData62323.2024.10825018.'),
  ('[8]  ', 'S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in Advances in Neural Information Processing Systems 30 (NeurIPS), 2017, pp. 4765–4774.'),
  ('[9]  ', 'M. Wagner, B. M. Ampel, M. Hashim and H. Chen, “Email phishing prevention: An explainable nudging approach,” in WISP 2025 Proceedings, AIS eLibrary, 2025, Paper 4.'),
  ('[10]  ', 'S. S. Roy, C. Torres and S. Nilizadeh, “‘Explain, don’t just warn!’ — A real-time framework for generating phishing warnings with contextual cues,” arXiv:2505.06836, May 2025.'),
  ('[11]  ', 'F. M. Cau, G. Desolda, F. Greco, L. D. Spano and L. Viganò, “Can large language models automate phishing warning explanations? A controlled experiment on effectiveness and user perception,” arXiv:2507.07916, 2025.'),
  ('[12]  ', 'G. Ho et al., “Detecting and characterizing lateral phishing at scale,” in Proc. 28th USENIX Security Symposium, 2019.'),
 ],
}
for n, items in refs.items():
    for i, (a, b) in enumerate(items):
        setp(n, 'Text 421', i, a, b)
# extra references [13], [14] on slide 22 (clone last paragraph)
sh = shape(S(22), 'Text 421')
last = sh.text_frame.paragraphs[5]._p
for num, txt in [('[13]  ', 'Anti-Phishing Working Group (APWG), “Phishing Activity Trends Report, 2nd Quarter 2026,” Aug. 2026.'),
                 ('[14]  ', 'Federal Bureau of Investigation, Internet Crime Complaint Center (IC3), “Internet Crime Report 2025,” Apr. 2026.')]:
    new = copy.deepcopy(last)
    last.addnext(new)
    last = new
    rs = new.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}r')
    rs[0].find('{http://schemas.openxmlformats.org/drawingml/2006/main}t').text = num
    rs[1].find('{http://schemas.openxmlformats.org/drawingml/2006/main}t').text = txt

# ------------------------------------------------------------------ slide 23 Thank you
dup_para(23, 'Shape 424', 0)
setp(23, 'Shape 424', 0, 'Md Saquib Ali (1TE24CS174)   ·   N Sai Yashwanth Simha (1TE24CS178)')
setp(23, 'Shape 424', 1, 'Nakshatra Chaudhary (1TE24CS179)   ·   Mourya M Goankar (1BY24CS173)')
setp(23, 'Shape 424', 2, 'Guide: Dr. Shanthi D L, Dept. of CSE, BMSIT&M')

# ------------------------------------------------------------------ metadata
cp = prs.core_properties
cp.title = 'PhishLens - Mini Project Review 1'
cp.last_modified_by = 'Team PhishLens (Batch 45)'

prs.save('/home/claude/work/ppt/PhishLens_Review1.pptx')
print('saved')
