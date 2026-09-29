import io
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, HRFlowable
from backend.app.schemas.result import AnalysisResult


# Brand colors
_AMBER_600 = colors.HexColor("#d97706")
_AMBER_500 = colors.HexColor("#f59e0b")
_SLATE_900 = colors.HexColor("#0f172a")
_SLATE_700 = colors.HexColor("#334155")
_SLATE_300 = colors.HexColor("#cbd5e1")
_SLATE_100 = colors.HexColor("#f1f5f9")
_RED = colors.HexColor("#dc2626")
_GREEN = colors.HexColor("#16a34a")


def generate_pdf_report(result: AnalysisResult) -> bytes:
    """Generates a Lucen AI branded forensic investigation PDF report."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=36, bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    # ── Custom Styles ──
    brand_style = ParagraphStyle(
        "Brand", parent=styles["Heading1"],
        fontSize=24, leading=28,
        textColor=_AMBER_600,
    )
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Heading1"],
        fontSize=11, leading=14,
        textColor=_SLATE_700,
    )
    heading_style = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"],
        fontSize=13, leading=16,
        textColor=_SLATE_900,
        spaceBefore=14, spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "ReportBody", parent=styles["Normal"],
        fontSize=9, leading=13,
        textColor=_SLATE_700,
    )
    small_style = ParagraphStyle(
        "Small", parent=styles["Normal"],
        fontSize=7.5, leading=10,
        textColor=colors.HexColor("#94a3b8"),
    )

    story = []

    # ── Header ──
    story.append(Paragraph("<b>Lucen AI</b>", brand_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("Forensic Investigation Report", ParagraphStyle(
        "Subtitle", parent=styles["Heading2"],
        fontSize=14, leading=18, textColor=_SLATE_900,
    )))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "<i>Evidence Intelligence for Insurance Claims</i>",
        ParagraphStyle("Tagline", parent=body_style, fontSize=9, textColor=_AMBER_600, italic=True),
    ))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=_SLATE_300))
    story.append(Spacer(1, 4))

    # Meta row
    story.append(Paragraph(
        f"Analysis ID: <b>{result.id}</b> &nbsp;|&nbsp; "
        f"Mode: <b>{result.mode.upper()}</b> &nbsp;|&nbsp; "
        f"Date: <b>{result.created_at[:19]} UTC</b>",
        body_style,
    ))
    story.append(Spacer(1, 12))

    # ── Verdict Box ──
    band_color = _RED if result.overall.band == "HIGH" else (
        _AMBER_600 if result.overall.band == "MEDIUM" else _GREEN
    )
    risk_pct = round(result.overall.risk * 100)
    verdict_data = [[
        Paragraph("<b>Overall Fraud Verdict</b>", body_style),
        Paragraph(
            f"<b><font color='{band_color.hexval()}'>{result.overall.band} RISK</font></b>"
            f" ({risk_pct}%)", body_style,
        ),
        Paragraph(f"Confidence: <b>{result.overall.confidence.upper()}</b>", body_style),
    ]]
    verdict_table = Table(verdict_data, colWidths=[170, 210, 155])
    verdict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _SLATE_100),
        ("BOX", (0, 0), (-1, -1), 1.2, _SLATE_300),
        ("LINEBELOW", (0, 0), (-1, 0), 2, band_color),
        ("PADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(verdict_table)
    story.append(Spacer(1, 12))

    # ── Executive Summary ──
    story.append(Paragraph("<b>Executive Summary &amp; Recommended Action</b>", heading_style))
    story.append(Paragraph(result.overall.summary, body_style))
    story.append(Spacer(1, 12))

    # ── Pipeline Breakdown ──
    story.append(Paragraph("<b>Pipeline Authenticity Breakdown</b>", heading_style))
    scores_data = [["Pipeline", "Fraud Risk", "Authenticity", "Risk Band", "Confidence"]]
    if result.image:
        scores_data.append([
            "Image Verification",
            f"{round(result.image.risk * 100)}%",
            f"{round(result.image.authenticity * 100)}%",
            result.image.band, result.image.confidence.title(),
        ])
    if result.document:
        scores_data.append([
            "Document Forensics",
            f"{round(result.document.risk * 100)}%",
            f"{round(result.document.authenticity * 100)}%",
            result.document.band, result.document.confidence.title(),
        ])
    if result.identity:
        scores_data.append([
            "Identity Biometrics",
            f"{round(result.identity.risk * 100)}%",
            f"{round(result.identity.authenticity * 100)}%",
            result.identity.band, result.identity.confidence.title(),
        ])

    scores_table = Table(scores_data, colWidths=[135, 95, 105, 95, 105])
    scores_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), _SLATE_900),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, _SLATE_300),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _SLATE_100]),
    ]))
    story.append(scores_table)
    story.append(Spacer(1, 14))

    # ── Evidence Catalog ──
    story.append(Paragraph("<b>Forensic Evidence Findings</b>", heading_style))
    ev_data = [["ID", "Severity", "Detector", "Probability", "Reason"]]
    for ev in result.evidence[:12]:
        sev_color = "#dc2626" if ev.severity == "high" else (
            "#d97706" if ev.severity == "medium" else "#0284c7"
        )
        ev_data.append([
            ev.id,
            Paragraph(f"<font color='{sev_color}'><b>{ev.severity.upper()}</b></font>", body_style),
            ev.source,
            f"{round(ev.calibrated_score * 100)}%",
            Paragraph(ev.reason, body_style),
        ])

    if len(ev_data) > 1:
        ev_table = Table(ev_data, colWidths=[78, 62, 80, 68, 247])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _SLATE_700),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, _SLATE_300),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, _SLATE_100]),
        ]))
        story.append(ev_table)
    else:
        story.append(Paragraph(
            "No anomalous evidence was flagged for this claim submission.", body_style,
        ))

    # ── Footer ──
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_SLATE_300))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Generated by <b>Lucen AI</b> — Evidence Intelligence for Insurance Claims &nbsp;|&nbsp; "
        "Adrosonic Build &nbsp;|&nbsp; Confidential",
        small_style,
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
