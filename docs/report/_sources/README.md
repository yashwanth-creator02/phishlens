# Report generator sources (Node, docx-js)

`lib.js` (helpers + the 37 references), `ch12.js`, `ch3.js`, `ch4a.js` (chapter content as code) and `mdgen.js` (renders them to the Markdown files in `docs/report/`).
They are the single source for the chapters: edit text here, run `node mdgen.js ../` (from this folder; needs `npm i docx`) to regenerate the Markdown.
The Word build script (`build.js`: cover page, static contents page with page numbers, headers/footers, parts 2/5/6) was **not completed**; `lib.js` already
provides styled paragraph/table/figure helpers for it. Figures are in `docs/diagrams/`.
