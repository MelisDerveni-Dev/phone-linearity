# Rebuild the typeset report

Edit `report.md`. It contains LaTeX equations (`\[ ... \]` and `\( ... \)`), real matrix environments, and `<!-- page -->` markers that split it into three or four pages. `report.css` controls the layout, tables and printing. Equations are rendered from source with local KaTeX.

The report never computes results itself. `figures/poses.svg` and `figures/ramp.svg` are hand-drawn diagrams. `figures.py` draws the two charts (`before-after.png`, `shaking.png`) from existing result tables and the shaking recording; the build runs it automatically. Every number in the text comes from the result folders listed in the root README. Generate those results first (`python -m calib analyse`, then `python -m calib evidence`), then build from the project root:

```powershell
npm.cmd --prefix report ci
.\.venv\Scripts\python.exe -m pip install -e ".[report]"
.\.venv\Scripts\python.exe report/build_report.py
```

Use `npm` outside the Windows PowerShell launcher restriction and `.venv/bin/python` on macOS/Linux. The PDF build uses an installed Microsoft Edge or Google Chrome on Windows. Elsewhere, or without either browser, install the document-only Chromium runtime with `python -m playwright install chromium`.

Outputs:

- `report.pdf`: A4 pages (the brief allows 3–4; the build checks this), with author metadata and blank signature lines.
- `report.html`: the same content as a self-contained offline page, with embedded KaTeX WOFF2 fonts and figures, accessible MathML, and no scripts or CDN requests.

The build stops if any of these fail:

- a figure is missing;
- KaTeX font-face definitions are lost, or a required KaTeX font is not loaded;
- there is a math error;
- any page overflows;
- the page count is outside 3–4.

Inspect the PDF visually after changes.

Dependencies live in `report/package.json`/`package-lock.json` and the Python `report` extra; none are added to the live Node viewer. The KaTeX license is included beside this file and embedded in the standalone HTML.
