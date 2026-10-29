module.exports = (L) => {
  const { P, H1, H2, H3, B, N, T } = L;
  const { Paragraph, TextRun, AlignmentType, BorderStyle } = L.d;
  const out = []; const add = (...x) => x.flat().forEach(e => out.push(e));

  add(H1('3. Problem Identification and Objectives'));
  add(H2('3.1 Problem identification'));
  add(P('Chapter 2 and the threat data in Section 1.1 point to one underlying problem: detection technology has become accurate, but the person who must act on its output is still given a verdict without a justification, and the workflow for obtaining a verdict is often inconvenient. The problem has four connected parts.'));
  add(B([
    '**Unexplained verdicts.** A filter that only states that a message is suspicious gives the reader nothing to verify. Explanations that are available in the research literature are mostly plots intended for analysts {{yi,bhavana}}, whereas controlled studies show that reasons expressed for users improve detection and understanding {{wagner,roy}}.',
    '**Narrow evidence.** Many detectors rely on one kind of evidence, such as URL features or message text {{yi,altwaijry}}. When attackers use LLMs to produce fluent text {{heiding,afane}}, wording alone is an unreliable signal, and evidence from headers, links, requested actions, attachments and sender history must be combined.',
    '**High-friction workflow.** Tools that ask the user to install a plug-in, paste headers into a form or copy links by hand are rarely used at the moment of doubt. A forward-to-bot workflow uses the Forward or Share action that every email application already provides.',
    '**Unproven benefit of explanations.** Few systems measure whether their explanations actually help people recognise phishing {{cau}}. A system that explains itself should also be able to show that the explanation is understandable and useful.']));
  add(P('The affected users are individuals, students, first-time internet users, small shops and small organisations that have no security team between them and a fraudulent message.'));

  add(H2('3.2 Gaps identified and proposed solutions'));
  add(P('The problem translates into three gaps that were stated in the project synopsis and that map onto the six literature gaps (G1 to G6) of Table 3.'));
  add(T('Gaps in existing approaches and the proposed solution',
    ['ID', 'Gap identified', 'Proposed solution', 'Literature gaps addressed'],
    [
      ['P1', 'Limited interpretability: existing approaches give a classification or risk result, but the reasons are not understandable to ordinary users.', 'Integrate SHAP to find the features that contribute most to each prediction and present them as clear, verified, plain-language reasons. Provide a dedicated bot email address so users can forward emails for automated analysis.', 'G1, G6'],
      ['P2', 'Dependence on individual detection approaches and limited indicators: effectiveness varies with data and features, and many systems examine only URLs or only text.', 'Evaluate an existing detection model alongside a model developed in this project, compare them with appropriate measures, and combine six groups of message characteristics (sender and headers, URLs, language, requested action, attachments, sender behaviour) as features.', 'G2, G3, G4, G5'],
      ['P3', 'Limited evaluation of user-oriented explanations: it is rarely measured whether the explanations help users identify phishing.', 'Present the important features as plain-language explanations and run a controlled user study comparing a risk label alone with a risk label plus reasons.', 'G1, G6']
    ],
    [600, 2700, 3600, 2006], { zebra: true }));

  add(H2('3.3 Problem statement'));
  add(new Paragraph({
    alignment: AlignmentType.JUSTIFIED, spacing: { line: 360, before: 80, after: 160 },
    indent: { left: 360, right: 360 },
    border: { left: { style: BorderStyle.SINGLE, size: 18, color: '2F5597', space: 10 } },
    children: L.runs('The project aims to develop a phishing detection system that combines multiple message characteristics, compares an existing detection approach with a model developed as part of the project, and provides explainable results that communicate the main reasons behind each prediction in a form understandable to users, delivered through a convenient email-forwarding workflow.', { italics: true })
  }));

  add(H2('3.4 Objectives'));
  add(P('The objectives of the project are:'));
  add(N([
    'To collect phishing and genuine messages from publicly available datasets, supplement them with representative sample messages, and identify measurable features across the major phishing-related clue categories while documenting their meaning and extraction rules.',
    'To study and evaluate existing phishing detection models and develop our own machine learning model, then compare their performance using appropriate evaluation metrics and select a suitable approach for the proposed system.',
    'To integrate SHapley Additive exPlanations (SHAP) with the selected approach to identify the features that influence each prediction and convert these technical explanations into clear, understandable statements for users.',
    'To evaluate the system using appropriate test data and performance measures, analyse common prediction errors, and develop a web interface through which users can access the analysis of emails forwarded to a dedicated bot email address, including the resulting risk level and supporting explanations.',
    'To evaluate whether the explanations improve users\' ability to identify phishing messages and, as an advanced goal, develop a browser add-on that can analyse messages directly within a webmail interface without sending the message elsewhere.']));

  add(H3('3.4.1 Measurable success criteria'));
  add(P('Each objective is tied to a measurable criterion. The targets below are planned values to be validated during evaluation, not results; they are set with reference to the performance levels reported in the literature (Chapter 2), and they will be revised if the data show that they are unrealistic.'));
  add(T('Success criteria for the objectives',
    ['Obj.', 'Success measure', 'Planned target', 'How verified'],
    [
      ['O1', 'Documented feature dictionary and assembled corpus', 'Six feature groups; at least 40 candidate features; at least three data sources; duplicates removed', 'Feature dictionary and dataset card reviewed by the guide'],
      ['O2', 'Macro F1 and ROC-AUC of the proposed model against the existing baseline', 'Proposed model at least equal to the baseline on both measures, with macro F1 of 0.95 or more on a held-out test set', 'Bootstrap 95% confidence intervals; McNemar test on paired predictions'],
      ['O3', 'Explanation coverage and faithfulness', 'At least 90% of Medium and High emails receive two or more verified reasons; neutralising the top features lowers the predicted probability', 'Deletion test and manual audit of a sample of explanations'],
      ['O4', 'Latency and error understanding', '95th-percentile end-to-end time of 5 seconds or less per email on a development server; documented false-positive and false-negative categories', 'Timing tests; error-analysis table'],
      ['O5', 'Effect of reasons on user accuracy', 'Group with reasons more accurate than label-only group by at least 10 percentage points (hypothesis informed by {{wagner}}); add-on prototype if time permits', 'Controlled user study (Section 4.17)']
    ],
    [600, 2600, 3300, 2406], { zebra: true }));

  add(H2('3.5 Scope, assumptions and constraints'));
  add(B([
    '**In scope:** English-language emails; message text, headers, URLs, requested actions, attachment metadata and sender history; Low, Medium and High risk bands with plain-language reasons; a web interface and the forward-to-bot workflow.',
    '**Out of scope:** analysis of images, QR codes, voice or video; opening, executing or detonating attachments (only metadata is inspected); automatic deletion or quarantine of messages in the user\'s mailbox; non-email channels such as SMS.',
    '**Forwarding changes the message.** When a mail client forwards a message inline, the new message is sent by the forwarder, so the original authentication results (SPF, DKIM, DMARC) are not preserved. Forwarding as an attachment keeps the original headers. The system therefore has to accept both forms, recover the original header block where it is quoted, and treat unrecoverable authentication features as explicitly missing rather than as failures (Section 4.5).',
    '**Public data only for training.** Public phishing corpora are historical and do not include the receiving user\'s earlier mail from the same sender, so behavioural features are evaluated on a semi-synthetic benchmark (Section 4.4).',
    '**Resource limits.** The project is built by a four-member student team with free or low-cost hosting; the design favours a single deployable service and synchronous processing.']));

  add(H2('3.6 Sustainable Development Goal (SDG) mapping'));
  add(P('The project maps to **SDG 9: Industry, Innovation and Infrastructure** {{un}}. Digital communication is part of the infrastructure referred to in Target 9.1, and phishing is a main way in which that layer is attacked; a single successful phishing email can disrupt a hospital\'s appointment system or empty a small business\'s account. The link is clearest with Target 9.c, which aims at affordable access to information and communications technology: access is only worth having if it can be used safely, and people who are new to the internet or who run small businesses have no security team to interpret a bare warning. Replacing a vague alert with a short list of clear reasons lets people without technical background take part in digital services more safely, at low cost, because the system is designed to run on ordinary computers. The project also supports Target 9.5 (strengthening research and innovation) by documenting its dataset, feature dictionary and evaluation method so that other students and researchers can reuse them.'));
  return out;
};
