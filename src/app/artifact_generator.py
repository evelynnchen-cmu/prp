"""
Evidence table artifact generator. Used by Search and Artifacts page.
Schema: Claim | Evidence snippet | Citation | Confidence | Notes.
"""
import re
from io import BytesIO
from typing import Any

import pandas as pd


def generate_evidence_table(
    query: str,
    answer: str,
    chunks: list[dict],
    citations: list[str],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build one row per retrieved chunk for the evidence table.
    Confidence = FAISS cosine similarity (similarity_score); use "—" if missing.
    """
    rows = []
    # Sentences for claim extraction (split on . ? !)
    sentences = re.split(r"(?<=[.!?])\s+", answer)

    for c in chunks:
        source_id = c.get("source_id", "")
        chunk_id = c.get("chunk_id", "")
        cit_str = f"({source_id}, {chunk_id})"

        # Claim: sentence containing this citation, or "—"
        claim = "—"
        for sent in sentences:
            if cit_str in sent or (source_id in sent and chunk_id in sent):
                claim = sent.strip()
                break
        if claim == "—" and answer.strip():
            claim = answer.strip()[:200] + ("..." if len(answer) > 200 else "")

        text = (c.get("text") or "")
        snippet = text[:200] + ("..." if len(text) > 200 else "")

        score = c.get("similarity_score")
        if score is not None:
            try:
                confidence = f"{float(score):.2f}"
            except (TypeError, ValueError):
                confidence = "—"
        else:
            confidence = "—"

        item = manifest.get(source_id) or {}
        title = item.get("title", "—")
        year = item.get("year", "—")
        notes = f"{title} ({year})"

        rows.append({
            "Claim": claim,
            "Evidence snippet": snippet,
            "Citation": cit_str,
            "Confidence": confidence,
            "Notes": notes,
        })

    return rows


def export_evidence_table(
    rows: list[dict[str, Any]],
    format: str,
) -> tuple[str | bytes, str]:
    """
    Export evidence table as CSV, Markdown, or PDF.
    Returns (data, suggested_filename) for st.download_button.
    format must be one of "csv", "markdown", "pdf".
    """
    if not rows:
        empty = "" if format != "pdf" else b""
        ext = {"csv": ".csv", "markdown": ".md", "pdf": ".pdf"}[format]
        return (empty, f"evidence_table{ext}")

    if format == "csv":
        df = pd.DataFrame(rows)
        data = df.to_csv(index=False)
        return (data, "evidence_table.csv")

    if format == "markdown":
        cols = list(rows[0].keys())
        lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
        for row in rows:
            cell = lambda v: str(v).replace("|", " ").replace("\n", " ")[:100]
            lines.append("| " + " | ".join(cell(row.get(c, "")) for c in cols) + " |")
        data = "\n".join(lines)
        return (data, "evidence_table.md")

    if format == "pdf":
        from xml.sax.saxutils import escape as xml_escape
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=30, bottomMargin=30)
        styles = getSampleStyleSheet()
        # Small style for table cells so text wraps
        cell_style = styles["Normal"]
        from reportlab.lib.styles import ParagraphStyle
        wrap_style = ParagraphStyle(
            "CellWrap",
            parent=cell_style,
            fontSize=8,
            leading=9,
            wordWrap="CJK",  # enables word wrap
        )

        def wrap_cell(text: str) -> Paragraph:
            safe = xml_escape(str(text)[:500])
            return Paragraph(safe, wrap_style)

        story = [Paragraph("Evidence table", styles["Title"]), Spacer(1, 12)]

        cols = list(rows[0].keys())
        # Header row as Paragraphs so styling is consistent
        header_row = [Paragraph(xml_escape(c), wrap_style) for c in cols]
        data_rows = [[wrap_cell(row.get(c, "")) for c in cols] for row in rows]
        table_data = [header_row] + data_rows

        # Column widths so text has room to wrap (in points; ~1.2 inch per column)
        col_width = 1.2 * inch
        t = Table(table_data, colWidths=[col_width] * len(cols))
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        doc.build(story)
        return (buf.getvalue(), "evidence_table.pdf")

    raise ValueError(f"format must be 'csv', 'markdown', or 'pdf'; got {format!r}")
