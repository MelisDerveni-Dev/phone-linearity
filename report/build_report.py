"""Build the four-page draft PDF from report.md (optional: pip install reportlab).

This is a document tool, not the deferred calibration/analysis implementation.
Run from repository root: python report/build_report.py
"""
from pathlib import Path
import re
from html import escape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT

BASE = Path(__file__).resolve().parent
FONT = Path('C:/Windows/Fonts')
if (FONT / 'times.ttf').exists():
    pdfmetrics.registerFont(TTFont('ReportSerif', str(FONT / 'times.ttf')))
    pdfmetrics.registerFont(TTFont('ReportBold', str(FONT / 'timesbd.ttf')))
    pdfmetrics.registerFont(TTFont('ReportSans', str(FONT / 'arial.ttf')))
    BODY, BOLD, SANS = 'ReportSerif', 'ReportBold', 'ReportSans'
else:
    BODY, BOLD, SANS = 'Times-Roman', 'Times-Bold', 'Helvetica'

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyReport', fontName=BODY, fontSize=11, leading=14.1, spaceAfter=7, textColor=colors.HexColor('#25312f')))
styles.add(ParagraphStyle(name='SectionReport', fontName=BOLD, fontSize=14, leading=18, spaceBefore=7, spaceAfter=9))
styles.add(ParagraphStyle(name='TitleReport', fontName=BOLD, fontSize=25, leading=29, spaceAfter=12))
styles.add(ParagraphStyle(name='EquationReport', fontName='Courier', fontSize=9.3, leading=13, leftIndent=9, spaceAfter=9, spaceBefore=2))

equations = [
    'm = S a + b + epsilon;   S: 3 x 3 matrix, b: 3-vector',
    '[m; 1] = [[S, b], [0, 1]] [a; 1]',
    'X_i = [a_ix, a_iy, a_iz, 1]\nM_i = mean(m_i)^T;   B = [S^T; b^T]',
    'S_hat a_hat = m - b_hat',
]

def inline_math(text):
    substitutions = {
        r'\mathbb{R}': 'R', r'\mathbb{R}^3': 'R^3', r'\times': ' x ',
        r'\varepsilon': 'epsilon', r'\theta': 'theta', r'\mathrm{m/s^2}': 'm/s²',
        r'\mathrm{rank}': 'rank', r'\arg\min': 'argmin', r'\bar m_i': 'mean(m_i)',
        r'\hat B': 'B_hat', r'\hat S': 'S_hat', r'\hat b': 'b_hat', r'\hat a': 'a_hat',
        r'\kappa_2': 'kappa_2', r'\arcsin': 'asin', r'\operatorname{atan2}': 'atan2',
        r'\sqrt': 'sqrt', r'\sum_i': 'sum_i', r'\|': '|', r'\pm': '+/-',
        r'\sin': 'sin', r'\circ': '°', r'\quad': ' ', r'\qquad': ' ',
        r'\,': ' ', r'\!': '', r'\in': ' in ', r'\begin{bmatrix}': '[', r'\end{bmatrix}': ']',
    }
    for old, new in substitutions.items():
        text = text.replace(old, new)
    text = text.replace(r'\\', '; ').replace('&', ', ').replace('{', '(').replace('}', ')')
    text = text.replace(chr(92), '')
    return text

def rich(text):
    text = re.sub(r'\\\((.*?)\\\)', lambda m: inline_math(m.group(1)), text)
    text = escape(text)
    text = re.sub(r'\*\*(.*?)\*\*', lambda m: f'<font name="{BOLD}">{m.group(1)}</font>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier" size="9">\1</font>', text)
    return text.replace('\n', '<br/>')

def make():
    raw = (BASE / 'report.md').read_text(encoding='utf-8')
    raw = raw.replace('## 3. Model and estimation', '\f## 3. Model and estimation')
    raw = raw.replace('## 4. Evidence: five required answers', '\f## 4. Evidence: five required answers')
    raw = raw.replace('**5 — Where does the model fail?**', '\f**5 — Where does the model fail?**')
    equation_index = 0
    story = []
    for page_idx, page in enumerate(raw.split('\f')):
        if page_idx:
            story.append(PageBreak())
        for block in re.split(r'\n\s*\n', page.strip()):
            if block.startswith(r'\['):
                story.append(Preformatted(equations[equation_index], styles['EquationReport']))
                equation_index += 1
            elif block.startswith('# '):
                story.append(Paragraph(rich(block[2:]), styles['TitleReport']))
            elif block.startswith('## '):
                story.append(Paragraph(rich(block[3:]), styles['SectionReport']))
            else:
                story.append(Paragraph(rich(block.replace('  \n', '\n').replace('\n', ' ')), styles['BodyReport']))

    def decoration(c, doc):
        c.setFillColor(colors.HexColor('#8e6d3d'))
        c.setFont(SANS, 8)
        c.drawString(43, 813, 'THE AFFINE OBSERVATORY  /  SCIENTIFIC REPORT DRAFT')
        c.drawRightString(552, 813, '20 OCT 2026')
        c.setStrokeColor(colors.HexColor('#cdbf9f'))
        c.line(43, 803, 552, 803)
        c.line(43, 39, 552, 39)
        c.setFillColor(colors.HexColor('#665e50'))
        c.drawString(43, 26, 'Measurements pending — not a completed experimental report')
        c.drawRightString(552, 26, str(doc.page))

    target = BASE / 'report-draft.pdf'
    doc = SimpleDocTemplate(str(target), pagesize=(595.28, 841.89), leftMargin=43, rightMargin=43, topMargin=49, bottomMargin=50, title='Is your phone linear? — report draft', author='Project team — names pending')
    doc.build(story, onFirstPage=decoration, onLaterPages=decoration)
    print(target)

if __name__ == '__main__':
    make()
