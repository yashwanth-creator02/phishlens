// Renders the report chapter sources (ch12.js, ch3.js, ch4a.js) to Markdown for docs/report/.
const fs = require('fs'); const path = require('path');
const real = require('./lib.js');
const { cite, REFS } = real;
const it = s => cite(s).replace(/__([^_]+)__/g, '*$1*');
const esc = s => String(s).replace(/\|/g, '\\|').replace(/\n/g, ' ');
const cell = c => esc(it(Array.isArray(c) ? c.join('<br>') : c));
const figs = []; let figN = 0, tabN = 0;
const L = {
  d: { Paragraph: function (o) { return '> ' + o.children + '\n\n'; }, TextRun: x => x, AlignmentType: {}, BorderStyle: {} },
  runs: s => it(s),
  P: s => it(s) + '\n\n',
  H1: t => `# ${t}\n\n`, H2: t => `## ${t}\n\n`, H3: t => `### ${t}\n\n`,
  B: items => items.map(s => `- ${it(s)}`).join('\n') + '\n\n',
  N: items => items.map((s, i) => `${i + 1}. ${it(s)}`).join('\n') + '\n\n',
  EQ: (t, n) => `> \`${t}\`${n ? `  *(${n})*` : ''}\n\n`,
  F: (file, text) => { figN++; return `![Figure ${figN}: ${it(text).replace(/[\[\]]/g, '')}](../diagrams/${path.basename(file)})\n\n*Figure ${figN}: ${it(text)}*\n\n`; },
  T: (text, headers, rows) => { tabN++; return `**Table ${tabN}: ${it(text)}**\n\n| ${headers.map(cell).join(' | ')} |\n|${headers.map(() => '---').join('|')}|\n` + rows.map(r => `| ${r.map(cell).join(' | ')} |`).join('\n') + '\n\n'; }
};
const out = {};
out['01-introduction-and-literature-survey.md'] = require('./ch12.js')(L).join('');
out['02-problem-identification-and-objectives.md'] = require('./ch3.js')(L).join('');
out['03-proposed-methodology-part-1.md'] = require('./ch4a.js')(L, '').join('');
const dir = process.argv[2];
for (const [f, t] of Object.entries(out)) fs.writeFileSync(path.join(dir, f), t);
// references
const refs = REFS.map((r, i) => `[${i + 1}] ${it(r[1])}`).join('\n\n');
fs.writeFileSync(path.join(dir, '..', 'references.md'), `# References (IEEE style)\n\nNumbering matches the citations in docs/report/ and the Review-1 deck (refs 1-14 of the deck are a subset; see docs/presentation/).\n\n${refs}\n`);
console.log('figures', figN, 'tables', tabN);
