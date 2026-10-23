# Rebuild the typeset report

Edit `report.md`. It contains LaTeX equations (`\[ ... \]` and `\( ... \)`), real matrix environments and four explicit `<!-- page -->` sections. `report.css` controls the editorial layout, tables and printing. Equations render from the source with KaTeX; they are not substituted by handwritten plain-text approximations.

From the project root:

```powershell
npm.cmd --prefix report ci
.\.venv\Scripts\python.exe -m pip install -e ".[report]"
.\.venv\Scripts\python.exe report/build_report.py
```

Use `npm` outside the Windows PowerShell launcher restriction and `.venv/bin/python` on macOS/Linux. Create the Python environment first using the root README. Static tables come from `python -m calib.analysis`. New four-height tables come from `python scripts/validate_new_angles.py`, which loads the recorded frozen model/policy and never retrains them.

The PDF build uses installed Microsoft Edge or Google Chrome on Windows. On other systems, or without either browser, install the document-only Chromium runtime:

```text
python -m playwright install chromium
```

Outputs:

- `report.html`: self-contained, offline HTML with embedded KaTeX WOFF2 fonts, figures, accessible MathML and no browser-side JavaScript or CDN requests.
- `report-draft.pdf`: four A4 pages with the same typeset content, named author metadata and blank signature lines.
- `figures/static-vector.png` and `figures/angle-tilt.png`: report-specific plots generated from the unchanged analysis CSVs, with readable single-panel layouts.

The build rejects lost font-face definitions, missing required loaded KaTeX fonts, math errors, page overflow and page counts other than four. Visually inspect the PDF after changes. An independent reviewer checked the current four-page PDF and self-contained HTML, including every matrix, chart and caption. All matrices fit their brackets; no clipping or collisions were found. The report includes the 23 October four-height validation alongside the static improvement and retains the earlier angle outcome separately.

Dependencies live in `report/package.json`/`package-lock.json` and the Python `report` extra. This does not add any dependencies to the live Node viewer. The KaTeX license is included beside this document and embedded in the standalone HTML. See the [official Node rendering documentation](https://katex.org/docs/node) for the chosen rendering method.
