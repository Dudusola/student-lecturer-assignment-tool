"""Export an assignment table to CSV, Excel, PDF or Word."""
import io
from datetime import date
from xml.sax.saxutils import escape

import pandas as pd
from docx import Document
from docx.shared import Pt, RGBColor
from openpyxl.styles import Alignment, Font, PatternFill
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

TITLE = "Student–Lecturer Assignment Report"
BRAND = "#1E3A8A"
COLUMNS = {"name": "Student", "matric": "Matric No.", "field": "Student field",
           "lecturer": "Lecturer", "lecturer_field": "Lecturer field", "match": "Match"}
FORMATS = {  # label -> (extension, mime)
    "Excel": ("xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "PDF": ("pdf", "application/pdf"),
    "Word": ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
    "CSV": ("csv", "text/csv"),
}


def _safe_cell(v):
    """Stop spreadsheet apps from running uploaded text as a formula (CSV/formula injection)."""
    v = "" if pd.isna(v) else str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@", "\t", "\r") else v


def _flat(table: pd.DataFrame, spreadsheet=False) -> pd.DataFrame:
    df = table.copy()
    df["match"] = [f"{lab} ({s:.0%})" if pd.notna(s) else lab for lab, s in zip(df["match"], df["score"])]
    df = df[list(COLUMNS)].rename(columns=COLUMNS)
    df = df.sort_values(["Lecturer", "Student"], key=lambda s: s.str.lower()).fillna("")
    return df.map(_safe_cell) if spreadsheet else df


def _groups(table: pd.DataFrame):
    """(heading, rows) per lecturer, then unassigned students last."""
    df = _flat(table)
    cols = ["Student", "Matric No.", "Student field", "Match"]
    for lec, g in df[df["Lecturer"] != ""].groupby("Lecturer", sort=False):
        field = g["Lecturer field"].iloc[0]
        yield (f"{lec} — {field}" if field else lec), len(g), [cols] + g[cols].values.tolist()
    un = df[df["Lecturer"] == ""]
    if len(un):
        yield "Unassigned", len(un), [cols] + un[cols].values.tolist()


def build(fmt: str, table: pd.DataFrame) -> bytes:
    if fmt == "CSV":
        return _flat(table, spreadsheet=True).to_csv(index=False).encode("utf-8-sig")  # BOM so Excel shows accents
    if fmt == "Excel":
        return _excel(table)
    if fmt == "PDF":
        return _pdf(table)
    if fmt == "Word":
        return _word(table)
    raise ValueError(f"Unsupported format: {fmt}")


def _excel(table):
    flat = _flat(table, spreadsheet=True)
    summary = (flat[flat["Lecturer"] != ""].groupby("Lecturer").size()
               .rename("Students").reset_index())
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for sheet, df in (("Assignments", flat), ("Workload", summary)):
            df.to_excel(xw, sheet_name=sheet, index=False)
            ws = xw.sheets[sheet]
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor=BRAND[1:])
                cell.alignment = Alignment(vertical="center")
            for i, col in enumerate(df.columns, 1):
                width = max([len(str(col))] + [len(str(v)) for v in df.iloc[:, i - 1]]) + 2
                ws.column_dimensions[ws.cell(1, i).column_letter].width = min(width, 45)
    return buf.getvalue()


def _pdf(table):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.6 * cm, rightMargin=1.6 * cm,
                            topMargin=1.6 * cm, bottomMargin=1.6 * cm, title=TITLE)
    ss = getSampleStyleSheet()
    ss["Title"].textColor = colors.HexColor(BRAND)
    ss["Heading2"].textColor = colors.HexColor(BRAND)
    cell = ss["BodyText"].clone("cell", fontSize=9, leading=11)
    head = cell.clone("head", fontName="Helvetica-Bold", textColor=colors.white)
    widths = [5.2 * cm, 3.4 * cm, 5 * cm, 4.2 * cm]

    story = [Paragraph(TITLE, ss["Title"]),
             Paragraph(f"Generated {date.today():%d %B %Y} · {len(table)} students", ss["Normal"]),
             Spacer(1, 14)]
    for heading, count, rows in _groups(table):
        # Paragraph parses XML-like markup, so escape user text
        story.append(Paragraph(f"{escape(heading)} <font size=10 color='#64748B'>({count})</font>", ss["Heading2"]))
        data = [[Paragraph(escape(str(v)), head if r == 0 else cell) for v in row] for r, row in enumerate(rows)]
        t = Table(data, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story += [t, Spacer(1, 12)]
    doc.build(story)
    return buf.getvalue()


def _word(table):
    doc = Document()
    doc.styles["Normal"].font.size = Pt(10)
    h = doc.add_heading(TITLE, level=1)
    h.runs[0].font.color.rgb = RGBColor.from_string(BRAND[1:])
    doc.add_paragraph(f"Generated {date.today():%d %B %Y} · {len(table)} students")
    for heading, count, rows in _groups(table):
        doc.add_heading(f"{heading} ({count})", level=2)
        t = doc.add_table(rows=0, cols=len(rows[0]))
        t.style = "Light Grid Accent 1"
        for r, row in enumerate(rows):
            cells = t.add_row().cells
            for c, v in enumerate(row):
                cells[c].text = str(v)
                if r == 0:
                    cells[c].paragraphs[0].runs[0].bold = True
        doc.add_paragraph()
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
