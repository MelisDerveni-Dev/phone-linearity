"""Typeset LaTeX with local KaTeX; create a self-contained HTML page and a 3-4 page PDF.

Setup: npm --prefix report ci; pip install -e ".[report]"
Uses installed Edge/Chrome, or Playwright Chromium (playwright install chromium).
The live viewer remains dependency-free. No report assets load from a CDN.
"""
import base64
from html import escape
import json
import mimetypes
from pathlib import Path
import re
import shutil
import subprocess


from playwright.sync_api import sync_playwright
from pypdf import PdfReader, PdfWriter

BASE = Path(__file__).resolve().parent
AUTHORS = "Melis Derveni and Harsimranjeet Kaur"


def data_uri(path):
    media = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix == ".woff2":
        media = "font/woff2"
    return f"data:{media};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def katex_css():
    dist = BASE / "node_modules/katex/dist"
    css = (dist / "katex.min.css").read_text(encoding="utf-8")
    # Modern Chromium needs only WOFF2. Keep fonts embedded for offline sharing.
    def modern_source(match):
        woff2 = re.search(r"url\([^)]*\.woff2\)[^,;}]*", match[1])
        if not woff2:
            raise ValueError("Expected a WOFF2 source in the KaTeX font CSS")
        return "src:" + woff2[0]
    expected_faces = css.count("@font-face")
    # Minified KaTeX ends src declarations at `}`, often without `;`.
    # Never consume the next font-face block (or the KaTeX base font rule).
    css = re.sub(r"src:([^;}]+)", modern_source, css)
    if expected_faces < 20 or css.count("@font-face") != expected_faces:
        raise ValueError("KaTeX font-face definitions were lost during embedding")
    def embed(match):
        path = dist / match[1].strip("\"'")
        return "url(" + data_uri(path) + ")"
    return re.sub(r"url\(([^)]+)\)", embed, css)


def make():
    node = shutil.which("node")
    if not node or not (BASE / "node_modules/katex").exists():
        raise SystemExit("Install document tooling first: npm --prefix report ci")
    # Charts are drawn from existing result tables; nothing is refitted.
    import figures
    figures.main()
    rendered = subprocess.run([node, str(BASE / "render_report.cjs"), str(BASE / "report.md")],
                              check=True, capture_output=True, encoding="utf-8")
    pages = json.loads(rendered.stdout)["pages"]
    css = katex_css() + "\n" + (BASE / "report.css").read_text(encoding="utf-8")
    sections = []
    for i, content in enumerate(pages, 1):
        def embed_image(match):
            path = (BASE / match[1]).resolve()
            return 'src="' + data_uri(path) + '"'
        content = re.sub(r'src="([^"\n]+)"', embed_image, content)
        sections.append(f'''<article class="page" aria-label="Report page {i}">
<header class="page-header"><span>The Affine Observatory</span><span>Final report · 23 October 2026</span></header>
<main class="page-content">{content}</main>
<footer class="page-footer"><span>Melis Derveni · Harsimranjeet Kaur</span><span>{i} / {len(pages)}</span></footer></article>''')
    license_text = (BASE / "node_modules/katex/LICENSE").read_text(encoding="utf-8")
    html = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="author" content="{escape(AUTHORS)}"><title>Is your phone linear?</title>
<style>{css}</style></head><body>{''.join(sections)}
<!-- KaTeX license: {escape(license_text)} --></body></html>'''
    html_path = BASE / "report.html"
    html_path.write_text(html, encoding="utf-8")
    with sync_playwright() as p:
        candidates = [Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
                      Path("C:/Program Files/Google/Chrome/Application/chrome.exe")]
        installed = next((str(path) for path in candidates if path.exists()), None)
        options = {"executable_path": installed} if installed else {}
        browser = p.chromium.launch(headless=True, **options)
        page = browser.new_page(viewport={"width": 1100, "height": 1200})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(html_path.as_uri(), wait_until="load")
        page.evaluate("document.fonts.ready")
        loaded_fonts = page.evaluate("""async () => {
            const families = ['KaTeX_Main', 'KaTeX_Math', 'KaTeX_Size1', 'KaTeX_Size2', 'KaTeX_Size3'];
            const result = {};
            for (const family of families) {
                const loaded = await document.fonts.load('16px ' + family);
                result[family] = loaded.length > 0 && document.fonts.check('16px ' + family);
            }
            return result;
        }""")
        if not all(loaded_fonts.values()):
            browser.close()
            raise RuntimeError(f"Required KaTeX fonts are unavailable: {loaded_fonts}")
        page.emulate_media(media="print")
        overflow = page.locator(".page-content").evaluate_all("els => els.map((e,i)=>({page:i+1,vertical:e.scrollHeight-e.clientHeight,horizontal:e.scrollWidth-e.clientWidth}))")
        if any(item["vertical"] > 2 or item["horizontal"] > 2 for item in overflow):
            browser.close()
            raise RuntimeError(f"Report exceeds page content areas: {overflow}")
        if page.locator(".katex-error").count() or errors:
            browser.close()
            raise RuntimeError(f"Math/browser rendering failed: {errors}")
        pdf_bytes = page.pdf(format="A4", print_background=True, prefer_css_page_size=True,
                             display_header_footer=False, tagged=True)
        browser.close()
    from io import BytesIO
    reader = PdfReader(BytesIO(pdf_bytes))
    if len(reader.pages) != len(pages) or not 3 <= len(reader.pages) <= 4:
        raise RuntimeError(f"Expected {len(pages)} pages within the 3-4 page limit; got {len(reader.pages)}")
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({"/Title": "Is your phone linear?", "/Author": AUTHORS,
                         "/Subject": "Measured affine accelerometer calibration and held-out validation"})
    target = BASE / "report.pdf"
    with target.open("wb") as stream:
        writer.write(stream)
    print(f"{html_path}\n{target}\nVerified: {len(reader.pages)} pages; local KaTeX fonts; no content overflow.")


if __name__ == "__main__":
    make()
