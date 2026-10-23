/* Document-only Markdown and KaTeX rendering; no browser-side script needed. */
const fs = require('node:fs');
const katex = require('katex');
const MarkdownIt = require('markdown-it');

const source = fs.readFileSync(process.argv[2], 'utf8');
const markdown = new MarkdownIt({html: true, typographer: true});
const pages = source.split(/<!--\s*page\s*-->/);
if (pages.length < 3 || pages.length > 4) throw new Error('The report must have three or four explicit pages (course limit).');
const rendered = pages.map(page => {
  const math = [];
  const slot = (tex, displayMode) => {
    const token = `REPORTMATHSLOT${math.length}END`;
    math.push(katex.renderToString(tex.trim(), {
      displayMode, throwOnError: true, strict: 'error', trust: false,
      output: 'htmlAndMathml',
    }));
    return displayMode ? `\n\n<div class="equation">${token}</div>\n\n` : token;
  };
  page = page.replace(/\\\[([\s\S]*?)\\\]/g, (_, tex) => slot(tex, true));
  page = page.replace(/\\\(([\s\S]*?)\\\)/g, (_, tex) => slot(tex, false));
  let html = markdown.render(page);
  html = html.replace(/REPORTMATHSLOT(\d+)END/g, (_, index) => math[Number(index)]);
  return html;
});
process.stdout.write(JSON.stringify({pages: rendered}));
