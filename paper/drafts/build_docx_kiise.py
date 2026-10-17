"""Fill the official KIISE review form (references/forms/kiise_review_form.docx) in place.

Unlike build_docx.py, the form's title table, fonts, margins and two-column body are kept;
only the placeholder text is replaced.  Usage: python build_docx_kiise.py <draft.md> [out.docx]
"""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

from build_docx import _blocks

HERE = Path(__file__).resolve().parent
FORM = HERE.parent / "references" / "forms" / "kiise_review_form.docx"
FONT = "함초롬돋움"  # the form's font
BODY_PT, SMALL_PT = 10, 9  # form body is 10pt; the form requires >= 9pt everywhere
WIDE = "<!-- wide -->"


def _fonts(run, size: float, bold: bool = False, italic: bool = False) -> None:
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.insert(0, fonts)
    for key in ("ascii", "eastAsia", "hAnsi", "cs"):
        fonts.set(qn(f"w:{key}"), FONT)


def _form_spacing(p, *, exact: bool = True) -> None:
    # The form's body paragraphs: word-level wrapping, exact 15pt line spacing.
    ppr = p._p.get_or_add_pPr()
    ppr.insert(0, OxmlElement("w:wordWrap"))
    fmt = p.paragraph_format
    fmt.space_before = fmt.space_after = Pt(0)
    if exact:
        fmt.line_spacing = Pt(15)
    else:
        fmt.line_spacing = 1.0


def _write(p, lines, size: float, bold: bool = False) -> None:
    for index, (text, _) in enumerate(lines):
        if index:
            p.add_run(" ")
        for token in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*)", text):
            if not token:
                continue
            is_bold = token.startswith("**") and token.endswith("**")
            is_italic = token.startswith("*") and token.endswith("*") and not is_bold
            value = token[2:-2] if is_bold else token[1:-1] if is_italic else token
            _fonts(p.add_run(value), size, bold or is_bold, is_italic)
    for run in p.runs:
        _fonts(run, size, bold or bool(run.bold), bool(run.italic))


def _replace_text(p_el, text: str) -> None:
    """Replace a form paragraph's runs with one run that keeps the first run's formatting."""
    runs = p_el.findall(qn("w:r"))
    rpr = copy.deepcopy(runs[0].find(qn("w:rPr"))) if runs else None
    for child in list(p_el):
        if child.tag in (qn("w:r"), qn("w:hyperlink"), qn("w:bookmarkStart"), qn("w:bookmarkEnd")):
            p_el.remove(child)
    if not text:
        return
    r = OxmlElement("w:r")
    if rpr is not None:
        r.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    r.append(t)
    p_el.append(r)


def _section_break(body_sectpr, cols: int):
    """Paragraph that ends the current section; the section it ends gets `cols` columns."""
    p = OxmlElement("w:p")
    ppr = OxmlElement("w:pPr")
    sect = copy.deepcopy(body_sectpr)
    sect.find(qn("w:cols")).set(qn("w:num"), str(cols))
    ppr.append(sect)
    p.append(ppr)
    return p


def _table(doc, rows, total_cm: float):
    table = doc.add_table(rows=len(rows), cols=max(map(len, rows)))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{edge}")
        b.set(qn("w:val"), "single")
        b.set(qn("w:sz"), "4")
        b.set(qn("w:space"), "0")
        b.set(qn("w:color"), "000000")
        borders.append(b)
    table._tbl.tblPr.append(borders)
    margins = OxmlElement("w:tblCellMar")  # narrow padding so 9pt numbers fit a single column
    for edge in ("left", "right"):
        m = OxmlElement(f"w:{edge}")
        m.set(qn("w:w"), "57")
        m.set(qn("w:type"), "dxa")
        margins.append(m)
    table._tbl.tblPr.append(margins)
    # First column (labels) gets a bit more room; the rest share evenly.
    n = len(rows[0])
    first = total_cm * (0.22 if n == 4 else 0.28)
    widths = [Cm(first)] + [Cm((total_cm - first) / (n - 1))] * (n - 1)
    for column, width in zip(table.columns, widths):  # tblGrid; LibreOffice ignores cell widths alone
        column.width = width
    for row_index, cells in enumerate(rows):
        row = table.rows[row_index]
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        if row_index and not any(cells[1:]):  # group row: one merged, left-aligned label
            merged = row.cells[0].merge(row.cells[-1])
            p = merged.paragraphs[0]
            _form_spacing(p, exact=False)
            p.paragraph_format.keep_with_next = True
            _fonts(p.add_run(cells[0]), SMALL_PT, bold=True)
            continue
        for col, text in enumerate(cells):
            cell = row.cells[col]
            cell.width = widths[col]
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if col else WD_ALIGN_PARAGRAPH.LEFT
            _form_spacing(p, exact=False)
            p.paragraph_format.keep_with_next = row_index < len(rows) - 1
            for part_index, part in enumerate(text.replace("<br>", "\n").splitlines()):
                if part_index:
                    p.add_run().add_break()
                _fonts(p.add_run(part), SMALL_PT, bold=row_index == 0)
    header = OxmlElement("w:tblHeader")
    table.rows[0]._tr.get_or_add_trPr().append(header)
    return table


def build(source: Path, output: Path) -> Path:
    lines = source.read_text(encoding="utf-8").splitlines()
    title = next(line[2:].strip() for line in lines if line.startswith("# "))
    english = next(line.strip().strip("*") for line in lines if line.startswith("*"))
    abs_start = next(i for i, line in enumerate(lines) if line.startswith("## 요약"))
    body_start = next(i for i, line in enumerate(lines) if line.startswith("## 1. "))
    abstract = " ".join(
        line.strip().removesuffix("<br>").strip() for line in lines[abs_start + 1:body_start] if line.strip()
    )

    doc = Document(FORM)
    body = doc.element.body

    # --- Title block: the form's outer table, rows = [KR title, authors, EN title, spacer, abstract]
    outer = body.find(qn("w:tbl"))
    trs = outer.findall(qn("w:tr"))
    tc = [tr.find(qn("w:tc")) for tr in trs]
    nested = tc[0].find(qn("w:tbl"))  # blue "delete this box before submitting" notice
    tc[0].remove(nested)
    _replace_text(tc[0].findall(qn("w:p"))[-1], title)
    for p_el in tc[1].findall(qn("w:p")):  # review copy: no names/affiliations
        _replace_text(p_el, "")
    en_ps = tc[2].findall(qn("w:p"))
    _replace_text(en_ps[0], english)
    for p_el in en_ps[1:]:
        tc[2].remove(p_el)
    abs_ps = tc[4].findall(qn("w:p"))
    _replace_text(abs_ps[1], abstract)

    # --- Body: drop the form's sample text, keep both section properties.
    first_break = next(
        p for p in body.findall(qn("w:p")) if p.find(f"{qn('w:pPr')}/{qn('w:sectPr')}") is not None
    )
    body_sectpr = body.find(qn("w:sectPr"))
    removing = False
    for child in list(body):
        if child is first_break:
            removing = True
            continue
        if removing and child is not body_sectpr:
            body.remove(child)

    wide_next = False
    for kind, value in _blocks(lines[body_start:]):
        if kind == "heading":
            _, text = value
            p = doc.add_paragraph()
            _form_spacing(p)
            if not text.startswith("1. "):
                p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.keep_with_next = True
            _fonts(p.add_run(text), BODY_PT, bold=True)
        elif kind == "image":
            alt, rel = value
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.keep_with_next = True
            shape = p.add_run().add_picture(str((HERE / rel).resolve()), width=Cm(8.4))
            shape._inline.docPr.set("descr", alt)
        elif kind == "table":
            if wide_next:
                table = _table(doc, value, 18.0)
                body_sectpr.addprevious(_section_break(body_sectpr, cols=1))
                wide_next = False
            else:
                _table(doc, value, 8.6)
            spacer = doc.add_paragraph()  # breathing room after each table
            _form_spacing(spacer)
            spacer.paragraph_format.line_spacing = Pt(6)
        elif kind == "paragraph":
            para_lines = value
            if para_lines[0][0] == WIDE:
                # End the two-column flow; the caption + table run full width.
                body_sectpr.addprevious(_section_break(body_sectpr, cols=2))
                wide_next = True
                para_lines = para_lines[1:]
            text = " ".join(t for t, _ in para_lines)
            p = doc.add_paragraph()
            _form_spacing(p)
            if text.startswith("그림 "):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_after = Pt(4)
                _write(p, para_lines, SMALL_PT)
            elif text.startswith("표 "):
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.keep_with_next = True
                p.paragraph_format.line_spacing = 1.0
                _write(p, para_lines, SMALL_PT)
            elif re.match(r"\[\d+\]\s", text):
                fmt = p.paragraph_format
                fmt.line_spacing = Pt(12)
                fmt.left_indent, fmt.first_line_indent = Cm(0.6), Cm(-0.6)
                fmt.space_after = Pt(1)
                _write(p, para_lines, SMALL_PT)
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                _write(p, para_lines, BODY_PT)

    props = doc.core_properties  # review copy must not carry an author identity
    props.author = props.last_modified_by = props.subject = props.comments = props.keywords = ""
    props.title = title
    doc.save(output)
    return output


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        raise SystemExit("Usage: python build_docx_kiise.py <draft.md> [out.docx]")
    src = Path(sys.argv[1]).resolve()
    print(build(src, Path(sys.argv[2]).resolve() if len(sys.argv) == 3 else src.with_suffix(".docx")))
