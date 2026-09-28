from __future__ import annotations

import html
import re
from io import BytesIO
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Inches, Pt
from fpdf import FPDF


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"


def sanitize_text(text: str) -> str:
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u00a0": " ", "\u2022": "-", "\u200b": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def terms_to_rows(terms: str) -> list[str]:
    return [item.strip() for item in terms.split(";") if item.strip()]


def _add_logo_docx(document: Document) -> None:
    if not LOGO_PATH.exists():
        return
    header = document.sections[0].header
    paragraph = header.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(LOGO_PATH), width=Inches(1.55))


def format_docx(text: str, doc_type: str, terms: str = "") -> bytes:
    document = Document()
    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    for style_name in ("Title", "Heading 1", "Heading 2"):
        document.styles[style_name].font.name = "Times New Roman"

    section = document.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)
    _add_logo_docx(document)

    title = document.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(doc_type.upper())
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(16)

    text = sanitize_text(text)
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = block.splitlines()
        first = lines[0].strip()
        if re.match(r"^(?:SECTION\s+)?\d+[\.\): -]", first, re.I):
            p = document.add_paragraph(style="Heading 1")
            p.add_run(first)
            if len(lines) > 1:
                document.add_paragraph("\n".join(lines[1:]))
        elif first.isupper() and len(first) < 100:
            document.add_paragraph(first, style="Heading 2")
        else:
            p = document.add_paragraph(block)
            p.paragraph_format.space_after = Pt(7)
            p.paragraph_format.line_spacing = 1.15

    rows = terms_to_rows(terms)
    if rows:
        document.add_paragraph().add_run("KEY TERMS").bold = True
        table = document.add_table(rows=1, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.style = "Table Grid"
        table.rows[0].cells[0].text = "No."
        table.rows[0].cells[1].text = "Term"
        for idx, term in enumerate(rows, 1):
            cells = table.add_row().cells
            cells[0].text = str(idx)
            cells[1].text = term
            for cell in cells:
                cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer.add_run("LegalEase - AI-assisted draft. Review by qualified counsel before use.")

    output = BytesIO()
    document.save(output)
    return output.getvalue()


class LegalPDF(FPDF):
    def __init__(self, doc_type: str):
        super().__init__()
        self.doc_type = doc_type
        self.set_auto_page_break(auto=True, margin=18)

    def header(self):
        if LOGO_PATH.exists():
            try:
                self.image(str(LOGO_PATH), x=85, y=8, w=40)
                self.ln(17)
            except Exception:
                self.ln(6)
        else:
            self.ln(6)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 8, self.doc_type.upper(), align="C")
        self.ln(8)
        self.set_x(self.l_margin)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", size=8)
        self.cell(0, 8, f"LegalEase - AI-assisted draft | Page {self.page_no()}", align="C")


def format_pdf(text: str, doc_type: str, terms: str = "") -> bytes:
    pdf = LegalPDF(doc_type)
    pdf.set_margins(18, 25, 18)
    pdf.add_page()
    body_width = pdf.w - pdf.l_margin - pdf.r_margin
    text = sanitize_text(text)
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        first = block.splitlines()[0].strip()
        if re.match(r"^(?:SECTION\s+)?\d+[\.\): -]", first, re.I) or (first.isupper() and len(first) < 100):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(body_width, 7, first)
            rest = "\n".join(block.splitlines()[1:]).strip()
            if rest:
                pdf.set_font("Helvetica", size=10.5)
                pdf.multi_cell(body_width, 5.8, rest)
        else:
            pdf.set_font("Helvetica", size=10.5)
            pdf.multi_cell(body_width, 5.8, block)
        pdf.ln(2)

    rows = terms_to_rows(terms)
    if rows:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "KEY TERMS")
        pdf.ln(7)
        pdf.set_font("Helvetica", size=9.5)
        for idx, term in enumerate(rows, 1):
            pdf.multi_cell(body_width, 5.5, f"{idx}. {term}")
    return bytes(pdf.output())


def format_html_preview(text: str) -> str:
    safe = html.escape(sanitize_text(text))
    safe = re.sub(r"(^|\n)(\d+(?:\.\d+)*[\.\): -]+[^<\n]+)", r"\1<h3>\2</h3>", safe, flags=re.MULTILINE)
    safe = safe.replace("\n\n", "</p><p>").replace("\n", "<br>")
    return f'<div class="legal-preview"><p>{safe}</p></div>'


def format_txt(text: str) -> bytes:
    return sanitize_text(text).encode("utf-8")
