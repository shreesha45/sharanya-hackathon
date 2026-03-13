"""
PDF export utility using ReportLab.
Generates a styled meeting-action PDF in memory and returns the bytes.
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#1E3A5F")   # navy
ACCENT    = colors.HexColor("#2563EB")   # blue
HIGH_COL  = colors.HexColor("#DC2626")   # red
MED_COL   = colors.HexColor("#D97706")   # amber
LOW_COL   = colors.HexColor("#16A34A")   # green
LIGHT_BG  = colors.HexColor("#F1F5F9")   # slate-100
WHITE     = colors.white


# ── Style helpers ──────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title", parent=base["Title"],
            textColor=PRIMARY, fontSize=22, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=base["Normal"],
            textColor=ACCENT, fontSize=10, spaceAfter=12,
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"],
            textColor=PRIMARY, fontSize=13, spaceBefore=14, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", parent=base["Normal"],
            fontSize=9, leading=14, spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=base["Normal"],
            fontSize=9, leading=14, leftIndent=12, spaceAfter=2,
            bulletIndent=4,
        ),
        "task_title": ParagraphStyle(
            "TaskTitle", parent=base["Normal"],
            fontSize=9, leading=13, textColor=PRIMARY, fontName="Helvetica-Bold",
        ),
        "task_body": ParagraphStyle(
            "TaskBody", parent=base["Normal"],
            fontSize=8, leading=12,
        ),
    }


def _priority_color(priority: str) -> colors.Color:
    return {"High": HIGH_COL, "Medium": MED_COL, "Low": LOW_COL}.get(priority, MED_COL)


# ── Public function ────────────────────────────────────────────────────────────
def generate_pdf(
    meeting_summary: str,
    decisions: list[str],
    tasks: list[dict[str, Any]],
    discussion_points: list[str] | None = None,
    title: str = "Meeting Action Report",
) -> bytes:
    """
    Build and return a PDF as raw bytes.

    Parameters
    ----------
    meeting_summary : Summary paragraph
    decisions       : List of decision strings
    tasks           : List of task dicts (title, description, team, priority, status)
    discussion_points: Optional list of discussion point strings
    title           : Document title shown in header
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    S = _styles()
    story: list = []
    W = A4[0] - 36 * mm  # usable width

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph(title, S["title"]))
    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y  %H:%M')}",
        S["subtitle"],
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY))
    story.append(Spacer(1, 8))

    # ── Summary ─────────────────────────────────────────────────────────────
    story.append(Paragraph("Meeting Summary", S["h2"]))
    story.append(Paragraph(meeting_summary or "No summary provided.", S["body"]))
    story.append(Spacer(1, 6))

    # ── Discussion points ────────────────────────────────────────────────────
    if discussion_points:
        story.append(Paragraph("Discussion Points", S["h2"]))
        for pt in discussion_points:
            story.append(Paragraph(f"• {pt}", S["bullet"]))
        story.append(Spacer(1, 6))

    # ── Decisions ────────────────────────────────────────────────────────────
    if decisions:
        story.append(Paragraph("Decisions Made", S["h2"]))
        for dec in decisions:
            story.append(Paragraph(f"✓  {dec}", S["bullet"]))
        story.append(Spacer(1, 6))

    # ── Tasks table ──────────────────────────────────────────────────────────
    if tasks:
        story.append(Paragraph(f"Action Items  ({len(tasks)} tasks)", S["h2"]))
        story.append(Spacer(1, 3))

        col_widths = [W * 0.27, W * 0.35, W * 0.14, W * 0.12, W * 0.12]
        header_row = [
            Paragraph("<b>Title</b>", S["task_title"]),
            Paragraph("<b>Description</b>", S["task_title"]),
            Paragraph("<b>Team</b>", S["task_title"]),
            Paragraph("<b>Priority</b>", S["task_title"]),
            Paragraph("<b>Status</b>", S["task_title"]),
        ]
        rows = [header_row]

        for t in tasks:
            p_color = _priority_color(t.get("priority", "Medium"))
            rows.append([
                Paragraph(t.get("title", ""), S["task_body"]),
                Paragraph(t.get("description", ""), S["task_body"]),
                Paragraph(t.get("team", ""), S["task_body"]),
                Paragraph(
                    f'<font color="#{p_color.hexval()[2:]}">'
                    f'<b>{t.get("priority","")}</b></font>',
                    S["task_body"],
                ),
                Paragraph(t.get("status", "Pending"), S["task_body"]),
            ])

        tbl = Table(rows, colWidths=col_widths, repeatRows=1)
        tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0),  PRIMARY),
            ("TEXTCOLOR",   (0, 0), (-1, 0),  WHITE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
            ("GRID",        (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("VALIGN",      (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING",  (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(tbl)

    doc.build(story)
    return buf.getvalue()
