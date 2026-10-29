const fs = require('fs');
const d = require('docx');
const {
  Paragraph, TextRun, Table, TableRow, TableCell, ImageRun, AlignmentType, HeadingLevel,
  WidthType, ShadingType, BorderStyle, LevelFormat, TabStopType, LeaderType, Tab, PageBreak, VerticalAlign
} = d;

const FONT = 'Times New Roman';
const CW = 8906; // content width in DXA (A4, left 1700, right 1300)

// ---------- references ----------
const REFS = [
  ['prabakaran', 'M. K. Prabakaran, P. Meenakshi Sundaram, and A. D. Chandrasekar, "An enhanced deep learning-based phishing detection mechanism to effectively identify malicious URLs using variational autoencoders," __IET Information Security__, vol. 17, no. 3, pp. 423–440, May 2023.'],
  ['calzarossa', 'M. C. Calzarossa, P. Giudici, and R. Zieni, "Explainable machine learning for phishing feature detection," __Quality and Reliability Engineering International__, vol. 40, no. 1, pp. 362–373, 2024.'],
  ['altwaijry', 'N. Altwaijry, I. Al-Turaiki, R. Alotaibi, and F. Alakeel, "Advancing phishing email detection: A comparative study of deep learning models," __Sensors__, vol. 24, no. 7, p. 2077, Mar. 2024.'],
  ['sahingoz', 'O. K. Sahingoz, E. Buber, and E. Kugu, "DEPHIDES: Deep learning based phishing detection system," __IEEE Access__, vol. 12, pp. 8052–8070, 2024.'],
  ['divakaran', 'D. M. Divakaran and A. Oest, "Phishing detection leveraging machine learning and deep learning: A review," __IEEE Security & Privacy__, vol. 20, no. 5, pp. 86–95, Sep./Oct. 2022.'],
  ['apwgq2', 'Anti-Phishing Working Group (APWG), "Phishing Activity Trends Report, 2nd Quarter 2026," Aug. 28, 2026. [Online]. Available: https://docs.apwg.org/reports/apwg_trends_report_q2_2026.pdf'],
  ['apwgq4', 'Anti-Phishing Working Group (APWG), "Phishing Activity Trends Report, 4th Quarter 2025," Feb. 2026. [Online]. Available: https://docs.apwg.org/reports/apwg_trends_report_q4_2025.pdf'],
  ['ic3', 'Federal Bureau of Investigation, Internet Crime Complaint Center (IC3), "Internet Crime Report 2025," Apr. 2026. [Online]. Available: https://www.ic3.gov'],
  ['heiding', 'F. Heiding, S. Lermen, A. Kao, C. M. Verdun, B. Schneier, and A. Vishwanath, "Evaluating large language models\' ability to automate spear phishing," __Expert Systems with Applications__, vol. 314, Art. no. 131546, 2026, doi: 10.1016/j.eswa.2026.131546.'],
  ['afane', 'K. Afane, W. Wei, Y. Mao, J. Farooq, and J. Chen, "Next-generation phishing: How LLM agents empower cyber attackers," in __Proc. IEEE Int. Conf. Big Data (BigData)__, Dec. 2024, doi: 10.1109/BigData62323.2024.10825018.'],
  ['bethany', 'M. Bethany et al., "Large language model lateral spear phishing: A comparative study in large-scale organizational settings," arXiv:2401.09727, 2024 (rev. Apr. 2025).'],
  ['toth', 'R. Toth et al., "Constructing and benchmarking: A labeled email dataset for text-based phishing and spam detection framework," arXiv:2511.21448, Nov. 2025 (rev. Feb. 2026).'],
  ['yi', 'L. Yi, A. Omotosho, and H. Balogun, "Phishing URL detection and interpretability with machine learning: A cross-dataset approach," __Security and Privacy__, vol. 9, no. 1, Art. no. e70175, 2026, doi: 10.1002/spy2.70175.'],
  ['uddin', 'K. M. M. Uddin, N. Biswas, S. T. Rikta, M. Nur-A-Alam, and R. Mostafiz, "Explainable machine learning for phishing site detection: A high-efficiency approach using boosting models and SHAP," __The Journal of Engineering__, vol. 2025, no. 1, 2025, doi: 10.1049/tje2.70110.'],
  ['bhavana', 'B. S. Bhavana, S. Srivastava, D. Ghosh, V. Kumar, and P. Gupta, "Context-aware phishing email detection using hybrid machine learning and explainable AI," in __Proc. 17th Int. Conf. Contemporary Computing (IC3)__, Noida, India, 2025, pp. 1–6, doi: 10.1109/IC366947.2025.11290431.'],
  ['lundberg17', 'S. M. Lundberg and S.-I. Lee, "A unified approach to interpreting model predictions," in __Advances in Neural Information Processing Systems 30 (NeurIPS)__, 2017, pp. 4765–4774.'],
  ['lundberg20', 'S. M. Lundberg et al., "From local explanations to global understanding with explainable AI for trees," __Nature Machine Intelligence__, vol. 2, no. 1, pp. 56–67, 2020.'],
  ['chen16', 'T. Chen and C. Guestrin, "XGBoost: A scalable tree boosting system," in __Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining__, 2016, pp. 785–794.'],
  ['breiman', 'L. Breiman, "Random forests," __Machine Learning__, vol. 45, no. 1, pp. 5–32, 2001.'],
  ['grinsztajn', 'L. Grinsztajn, E. Oyallon, and G. Varoquaux, "Why do tree-based models still outperform deep learning on typical tabular data?," in __Advances in Neural Information Processing Systems 35 (NeurIPS)__, 2022, pp. 507–520.'],
  ['salih', 'A. M. Salih et al., "A perspective on explainable artificial intelligence methods: SHAP and LIME," __Advanced Intelligent Systems__, vol. 7, Art. no. 2400304, 2024.'],
  ['shafin', 'S. S. Shafin, "An explainable feature selection framework for web phishing detection with machine learning," __Data Science and Management__, vol. 8, no. 2, pp. 127–136, 2024.'],
  ['mia', 'M. Mia, D. Derakhshan, and M. M. A. Pritom, "Can features for phishing URL detection be trusted across diverse datasets? A case study with explainable AI," in __Proc. 11th Int. Conf. Networking, Systems, and Security__, ACM, 2024, pp. 137–145.'],
  ['greco', 'F. Greco, G. Desolda, and A. Esposito, "Explaining phishing attacks: An XAI approach to enhance user awareness and trust," in __Proc. Italian Conf. Cybersecurity (ITASEC)__, 2023.'],
  ['cau', 'F. M. Cau, G. Desolda, F. Greco, L. D. Spano, and L. Viganò, "Can large language models automate phishing warning explanations? A controlled experiment on effectiveness and user perception," arXiv:2507.07916, 2025.'],
  ['roy', 'S. S. Roy, C. Torres, and S. Nilizadeh, "\'Explain, don\'t just warn!\' — A real-time framework for generating phishing warnings with contextual cues," arXiv:2505.06836, May 2025.'],
  ['wagner', 'M. Wagner, B. M. Ampel, M. Hashim, and H. Chen, "Email phishing prevention: An explainable nudging approach," in __WISP 2025 Proceedings__, AIS eLibrary, 2025, Paper 4. [Online]. Available: https://aisel.aisnet.org/wisp2025/4'],
  ['ho', 'G. Ho et al., "Detecting and characterizing lateral phishing at scale," in __Proc. 28th USENIX Security Symposium__, 2019.'],
  ['dmarc', 'M. Kucherawy and E. Zwicky, "Domain-based Message Authentication, Reporting, and Conformance (DMARC)," IETF RFC 7489, Mar. 2015.'],
  ['spf', 'S. Kitterman, "Sender Policy Framework (SPF) for authorizing use of domains in email, version 1," IETF RFC 7208, Apr. 2014.'],
  ['dkim', 'D. Crocker, T. Hansen, and M. Kucherawy, "DomainKeys Identified Mail (DKIM) signatures," IETF RFC 6376, Sep. 2011.'],
  ['enron', 'B. Klimt and Y. Yang, "The Enron corpus: A new dataset for email classification research," in __Machine Learning: ECML 2004__, Lecture Notes in Computer Science, vol. 3201. Springer, 2004, pp. 217–226.'],
  ['nazario', 'J. Nazario, "Phishing corpus." [Online]. Available: https://monkey.org/~jose/phishing/'],
  ['spamassassin', 'Apache SpamAssassin Project, "SpamAssassin public mail corpus." [Online]. Available: https://spamassassin.apache.org/old/publiccorpus/'],
  ['phishtank', 'PhishTank, "PhishTank: Join the fight against phishing." [Online]. Available: https://www.phishtank.com'],
  ['sklearn', 'F. Pedregosa et al., "Scikit-learn: Machine learning in Python," __Journal of Machine Learning Research__, vol. 12, pp. 2825–2830, 2011.'],
  ['un', 'United Nations General Assembly, "Transforming our world: The 2030 Agenda for Sustainable Development," Resolution A/RES/70/1, 2015.']
];
const IDX = {}; REFS.forEach((r, i) => IDX[r[0]] = i + 1);

function cite(s) {
  return s.replace(/\{\{([^}]+)\}\}/g, (_, keys) => {
    const ns = keys.split(',').map(k => { k = k.trim(); if (!IDX[k]) throw new Error('bad ref ' + k); return IDX[k]; }).sort((a, b) => a - b);
    return ns.map(n => `[${n}]`).join(', ');
  });
}

// inline markup: **bold**, __italic__
function runs(str, o = {}) {
  str = cite(str);
  const parts = str.split(/(\*\*[^*]+\*\*|__[^_]+__)/g).filter(x => x !== '');
  return parts.map(p => {
    if (p.startsWith('**')) return new TextRun({ text: p.slice(2, -2), bold: true, font: o.font || FONT, size: o.size || 24, color: o.color });
    if (p.startsWith('__')) return new TextRun({ text: p.slice(2, -2), italics: true, font: o.font || FONT, size: o.size || 24, bold: o.bold, color: o.color });
    return new TextRun({ text: p, font: o.font || FONT, size: o.size || 24, bold: o.bold, italics: o.italics, color: o.color });
  });
}

// ---------- state ----------
const state = { heads: [], figs: [], tabs: [], numCfgs: [], figN: 0, tabN: 0, listN: 0 };

const P = (s, o = {}) => new Paragraph({
  children: runs(s, { size: o.size, bold: o.bold, italics: o.italics }),
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { line: o.line || 360, after: o.after === undefined ? 120 : o.after, before: o.before || 0 },
  indent: o.indent, keepNext: o.keepNext
});

function H1(text) {
  state.heads.push({ level: 1, text });
  return new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text, font: FONT })] });
}
function H2(text) { state.heads.push({ level: 2, text }); return new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, children: [new TextRun({ text, font: FONT })] }); }
function H3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3, keepNext: true, children: [new TextRun({ text, font: FONT })] }); }

function B(items, o = {}) { // bullets
  return items.map(s => new Paragraph({
    numbering: { reference: 'bullets', level: 0 },
    children: runs(s, { size: o.size }), alignment: AlignmentType.JUSTIFIED,
    spacing: { line: o.line || 340, after: 60 }
  }));
}
function N(items, o = {}) { // numbered list, restarts each call
  const ref = 'num' + (++state.listN);
  state.numCfgs.push({
    reference: ref,
    levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }]
  });
  return items.map(s => new Paragraph({
    numbering: { reference: ref, level: 0 },
    children: runs(s, { size: o.size }), alignment: AlignmentType.JUSTIFIED,
    spacing: { line: o.line || 340, after: 60 }
  }));
}

function EQ(text, num) {
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 140, line: 300 },
    tabStops: [{ type: TabStopType.RIGHT, position: CW }],
    children: [new TextRun({ text, italics: true, font: FONT, size: 24 }), ...(num ? [new TextRun({ children: [new Tab(), `(${num})`], font: FONT, size: 24 })] : [])]
  });
}

function CODE(lines) {
  return lines.map((l, i) => new Paragraph({
    spacing: { line: 240, after: 0 },
    indent: { left: 200, right: 200 },
    shading: { type: ShadingType.CLEAR, fill: 'F2F2F2', color: 'auto' },
    keepLines: true,
    children: [new TextRun({ text: l === '' ? ' ' : l, font: 'Courier New', size: 17 })]
  }));
}

function caption(label, n, text) {
  return new Paragraph({
    style: 'Caption', alignment: AlignmentType.CENTER, keepNext: label === 'Table',
    spacing: { before: label === 'Table' ? 160 : 60, after: label === 'Table' ? 80 : 200, line: 276 },
    children: [new TextRun({ text: `${label} ${n}: `, bold: true, font: FONT, size: 21 }), ...runs(text, { size: 21 })]
  });
}

function pngSize(file) { const b = fs.readFileSync(file); return [b.readUInt32BE(16), b.readUInt32BE(20)]; }

function F(file, text, o = {}) {
  const [w, h] = pngSize(file);
  let wi = o.w || 6.1; const maxH = o.maxH || 7.6;
  if (wi * h / w > maxH) wi = maxH * w / h;
  const n = ++state.figN; state.figs.push({ n, text });
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type: 'png', data: fs.readFileSync(file), transformation: { width: Math.round(wi * 96), height: Math.round(wi * 96 * h / w) },
        altText: { title: `Figure ${n}`, description: text.replace(/[*_]/g, ''), name: `fig${n}` } })]
    }),
    caption('Figure', n, text)
  ];
}

const BORDER = { style: BorderStyle.SINGLE, size: 4, color: '8FA3BF' };
const BORDERS = { top: BORDER, bottom: BORDER, left: BORDER, right: BORDER };

function cellParas(c, size, bold) {
  const arr = Array.isArray(c) ? c : [c];
  return arr.map((s, i) => new Paragraph({ spacing: { line: 252, after: i === arr.length - 1 ? 0 : 60 }, alignment: AlignmentType.LEFT, children: runs(String(s), { size, bold }) }));
}

function T(text, headers, rows, widths, o = {}) {
  const sum = widths.reduce((a, b) => a + b, 0);
  if (sum !== CW) throw new Error(`table "${text}" widths sum ${sum} != ${CW}`);
  const n = ++state.tabN; state.tabs.push({ n, text });
  const size = o.size || 19;
  const mk = (c, i, hdr, ri) => new TableCell({
    width: { size: widths[i], type: WidthType.DXA }, borders: BORDERS, verticalAlign: VerticalAlign.TOP,
    shading: hdr ? { type: ShadingType.CLEAR, fill: 'D9E2F3', color: 'auto' } : (o.zebra && ri % 2 === 1 ? { type: ShadingType.CLEAR, fill: 'F5F7FA', color: 'auto' } : undefined),
    margins: { top: 60, bottom: 60, left: 90, right: 90 },
    children: cellParas(c, size, hdr)
  });
  const trs = [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((h, i) => mk(h, i, true, 0)) }),
    ...rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => mk(c, i, false, ri)) }))];
  return [caption('Table', n, text), new Table({ width: { size: CW, type: WidthType.DXA }, columnWidths: widths, rows: trs }),
    new Paragraph({ spacing: { after: 160 }, children: [] })];
}

module.exports = { d, FONT, CW, REFS, IDX, cite, runs, state, P, H1, H2, H3, B, N, EQ, CODE, F, T, caption };
