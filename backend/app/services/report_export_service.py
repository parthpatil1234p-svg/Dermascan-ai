from dataclasses import dataclass
from html import escape as html_escape
from pathlib import Path
from uuid import uuid4

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.core.config import Settings
from app.models.final_report import MEDICAL_DISCLAIMER
from app.schemas.final_report import PrivacyMode
from app.utils.file_utils import ensure_directory, secure_child_path


class ReportExportError(Exception):
    pass


@dataclass(frozen=True)
class ExportedPdf:
    physical_path: Path
    download_filename: str


def _safe(value: object) -> str:
    return html_escape(str(value if value is not None else "Not available"), quote=True)


def render_report_html(document: dict, privacy_mode: PrivacyMode) -> str:
    template_path = Path(__file__).resolve().parents[1] / "templates" / "final_report.html"
    template = template_path.read_text(encoding="utf-8")
    profile = document.get("skin_profile_summary", {})
    body = [f"<h2>Executive Summary</h2><p>{_safe(document.get('summary', ''))}</p>"]
    if privacy_mode != "privacy_reduced":
        body.append(f"<h2>Skin Profile</h2><p>Age group: {_safe(profile.get('age_group'))}</p>")
        body.append(
            f"<p>Known allergies: {_safe(', '.join(profile.get('known_allergies', [])) or 'None reported')}</p>"
        )
    skin = document.get("skin_type_summary", {})
    body.append(f"<h2>Estimated Skin Type</h2><p>{_safe(skin.get('skin_type', 'Unavailable'))}</p>")
    body.append(f"<h2>Safety and Disclaimer</h2><p>{_safe(MEDICAL_DISCLAIMER)}</p>")
    return (
        template.replace("{{TITLE}}", _safe(document["report_title"]))
        .replace(
            "{{REPORT_META}}",
            _safe(f"{document['final_report_id']} | Version {document['report_version']}"),
        )
        .replace("{{BODY}}", "".join(body))
        .replace("{{DISCLAIMER}}", _safe(MEDICAL_DISCLAIMER))
    )


def _footer(canvas, doc, report_id: str, version: int) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#475569"))
    canvas.drawString(18 * mm, 12 * mm, f"{report_id} | Version {version}")
    canvas.drawRightString(192 * mm, 12 * mm, f"Page {doc.page}")
    canvas.drawCentredString(
        105 * mm, 8 * mm, "General skincare guidance only. Not a medical diagnosis."
    )
    canvas.restoreState()


def _paragraph(text: object, style) -> Paragraph:
    return Paragraph(_safe(text), style)


def create_pdf_export(document: dict, privacy_mode: PrivacyMode, settings: Settings) -> ExportedPdf:
    if document.get("report_status") not in {"complete", "complete_with_limitations"}:
        raise ReportExportError("Only complete reports can be exported.")
    ensure_directory(settings.report_export_path)
    random_name = f"{uuid4().hex}.pdf"
    target = secure_child_path(settings.report_export_path, random_name)
    styles = getSampleStyleSheet()

    # Custom Luxury & Clean Typography Styles
    title_style = ParagraphStyle(
        name="LuxuryTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F766E"),
        alignment=0,  # Left align for modern clean look
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        name="LuxurySubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=10,
    )
    meta_pill_style = ParagraphStyle(
        name="MetaPill",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0F766E"),
    )
    section_heading = ParagraphStyle(
        name="LuxurySection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )
    body_style = ParagraphStyle(
        name="LuxuryBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=4,
    )
    body_bold = ParagraphStyle(
        name="LuxuryBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )
    table_header = ParagraphStyle(
        name="TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F766E"),
    )
    table_cell = ParagraphStyle(
        name="TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )
    table_cell_bold = ParagraphStyle(
        name="TableCellBold",
        parent=table_cell,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )
    step_num_style = ParagraphStyle(
        name="StepNum",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0F766E"),
        alignment=TA_CENTER,
    )
    disclaimer_style = ParagraphStyle(
        name="DisclaimerText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#64748B"),
    )

    story = []

    # 1. Header Banner with Brand & Metadata
    report_title = document.get("report_title", "DermaScan AI Skincare Report")
    report_id = document.get("final_report_id", "DSR-REPORT")
    version = document.get("report_version", 1)
    gen_time = document.get("generated_at")
    gen_date_str = gen_time.strftime("%d %b %Y, %H:%M UTC") if hasattr(gen_time, "strftime") else str(gen_time)

    header_table = Table(
        [
            [
                Paragraph(f"<b>DERMASCAN AI</b> · Clinical Skincare Consultation", meta_pill_style),
                Paragraph(f"Report ID: <b>{_safe(report_id)}</b> | Version: <b>{_safe(version)}</b>", subtitle_style),
            ],
            [
                Paragraph(_safe(report_title), title_style),
                Paragraph(f"Generated: {_safe(gen_date_str)}", subtitle_style),
            ],
        ],
        colWidths=[110 * mm, 64 * mm],
        style=TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
            ]
        ),
    )
    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # 2. Executive Summary Card (Light Teal Highlight Container)
    summary_text = document.get("summary", "Personalized skin telemetry and routine summary.")
    summary_table = Table(
        [
            [
                Paragraph("<b>Executive Consultation Summary</b>", table_header),
            ],
            [
                Paragraph(_safe(summary_text), body_style),
            ],
        ],
        colWidths=[174 * mm],
        style=TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0FDFA")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#99F6E4")),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        ),
    )
    story.append(summary_table)
    story.append(Spacer(1, 4 * mm))

    # 3. Skin Profile & Biometric Results Table
    profile = document.get("skin_profile_summary", {})
    skin = document.get("skin_type_summary", {})

    profile_rows = [
        [
            Paragraph("Estimated Skin Type", table_header),
            Paragraph(f"<b>{_safe(skin.get('skin_type', 'Unavailable'))}</b> (Confidence: {_safe(skin.get('confidence_level', 'High'))})", table_cell),
            Paragraph("Questionnaire Agreement", table_header),
            Paragraph(_safe(skin.get("questionnaire_agreement", "Consistent")), table_cell),
        ]
    ]

    if privacy_mode != "privacy_reduced" and settings.report_pdf_include_profile_details:
        profile_rows.extend(
            [
                [
                    Paragraph("Age / Region", table_header),
                    Paragraph(f"{_safe(profile.get('age_group'))} · {_safe(profile.get('country'))}", table_cell),
                    Paragraph("Oiliness / Dryness", table_header),
                    Paragraph(f"{_safe(profile.get('oiliness_level'))} / {_safe(profile.get('dryness_level'))}", table_cell),
                ],
                [
                    Paragraph("Known Allergies", table_header),
                    Paragraph(_safe(", ".join(profile.get("known_allergies", [])) or "None reported"), table_cell),
                    Paragraph("Avoidance Ingredients", table_header),
                    Paragraph(_safe(", ".join(profile.get("ingredients_to_avoid", [])) or "None selected"), table_cell),
                ],
            ]
        )

    story.append(Paragraph("Skin Telemetry & Profile Overview", section_heading))
    story.append(
        Table(
            profile_rows,
            colWidths=[40 * mm, 47 * mm, 42 * mm, 45 * mm],
            style=TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F8FAFC")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 5),
                ]
            ),
        )
    )
    story.append(Spacer(1, 3 * mm))

    # 4. AI-Assisted Visible Skin Observations
    observations = document.get("visible_concern_summary", {})
    obs_list = []
    for label in ("observed", "possible", "uncertain"):
        for item in observations.get(label, []):
            regions_str = ", ".join(item.get("regions", [])) or "Full Face"
            obs_list.append([
                Paragraph(f"<b>{_safe(item.get('name', 'Observation'))}</b>", table_cell_bold),
                Paragraph(f"{_safe(item.get('visible_severity', 'Visible'))} appearance", table_cell),
                Paragraph(_safe(regions_str), table_cell),
                Paragraph(f"{_safe(item.get('confidence', '90'))}%" if item.get('confidence') else "Detected", table_cell),
            ])

    if obs_list:
        story.append(Paragraph("AI-Assisted Visible Facial Observations", section_heading))
        obs_table_data = [[
            Paragraph("Concern / Feature", table_header),
            Paragraph("Appearance", table_header),
            Paragraph("Facial Region", table_header),
            Paragraph("Confidence", table_header),
        ]] + obs_list
        story.append(
            Table(
                obs_table_data,
                colWidths=[55 * mm, 45 * mm, 48 * mm, 26 * mm],
                style=TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("PADDING", (0, 0), (-1, -1), 4.5),
                    ]
                ),
            )
        )
        story.append(Spacer(1, 3 * mm))

    # 5. Morning & Night Routine Tables (The Heart of User-Friendly UX)
    for title, key, bg_color, header_color in (
        ("Morning Skincare Regimen (Protection & Hydration)", "morning_routine", "#FEF3C7", "#D97706"),
        ("Night Skincare Regimen (Repair & Recovery)", "night_routine", "#EDE9FE", "#7C3AED"),
    ):
        steps = document.get(key, [])
        if steps:
            story.append(Paragraph(title, section_heading))
            routine_rows = [[
                Paragraph("Step", table_header),
                Paragraph("Category & Product Name", table_header),
                Paragraph("Application & Purpose", table_header),
            ]]
            for step in steps:
                step_num = step.get("step_number", 1)
                opt = " (Optional)" if step.get("is_optional") else ""
                cat = step.get("category", "TREATMENT").upper()
                p_name = step.get("product_name", "Prescribed Product")
                brand = f" by {step.get('brand_name')}" if step.get("brand_name") else ""
                guidance = step.get("usage_guidance") or step.get("purpose") or "Apply evenly to face."

                routine_rows.append([
                    Paragraph(f"<b>0{step_num}</b>", step_num_style),
                    Paragraph(f"<b>{_safe(p_name)}</b>{_safe(brand)}<br/><font color='#0F766E' size='7'>{_safe(cat)}{_safe(opt)}</font>", table_cell),
                    Paragraph(_safe(guidance), table_cell),
                ])

            story.append(
                Table(
                    routine_rows,
                    colWidths=[16 * mm, 78 * mm, 80 * mm],
                    style=TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("PADDING", (0, 0), (-1, -1), 5),
                        ]
                    ),
                )
            )
            story.append(Spacer(1, 3 * mm))

    # 6. Recommended Products & Ingredient Guidance
    recs = document.get("product_recommendation_summary", [])
    if recs:
        story.append(Paragraph("Curated Product Recommendations", section_heading))
        rec_rows = [[
            Paragraph("Rank", table_header),
            Paragraph("Product & Brand", table_header),
            Paragraph("Category", table_header),
            Paragraph("Match Score", table_header),
            Paragraph("Why Recommended", table_header),
        ]]
        for item in recs[:6]:  # Show top recommendations cleanly
            p_name = item.get("product_name", "Skincare Item")
            brand = item.get("brand_name", "")
            cat = item.get("category", "Treatment").title()
            score = item.get("score", 90)
            why = item.get("why_recommended", "High compatibility with identified skin parameters.")
            rec_rows.append([
                Paragraph(f"#{item.get('rank', 1)}", step_num_style),
                Paragraph(f"<b>{_safe(p_name)}</b><br/><font size='7' color='#64748B'>{_safe(brand)}</font>", table_cell),
                Paragraph(_safe(cat), table_cell),
                Paragraph(f"<b>{score}/100</b>", table_cell_bold),
                Paragraph(_safe(why), table_cell),
            ])

        story.append(
            Table(
                rec_rows,
                colWidths=[14 * mm, 50 * mm, 26 * mm, 24 * mm, 60 * mm],
                style=TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F8FAFC")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 4.5),
                    ]
                ),
            )
        )
        story.append(Spacer(1, 3 * mm))

    # 7. Targeted Ingredients Breakdown
    guidance = document.get("ingredient_guidance", {})
    beneficial = guidance.get("potentially_relevant", [])
    avoid = guidance.get("avoid_or_review", [])

    if beneficial or avoid:
        story.append(Paragraph("Formulation & Ingredient Insights", section_heading))
        ing_rows = []
        for b in beneficial[:4]:
            ing_rows.append([
                Paragraph("<b>Beneficial</b>", ParagraphStyle(name="IngB", parent=table_cell_bold, textColor=colors.HexColor("#059669"))),
                Paragraph(f"<b>{_safe(b.get('ingredient_role'))}</b>: {_safe(b.get('reason'))}", table_cell),
            ])
        if privacy_mode == "privacy_reduced":
            ing_rows.append([
                Paragraph("<b>Privacy Mode</b>", table_cell_bold),
                Paragraph("Detailed allergy and avoidance guidance is hidden in this privacy-reduced export.", table_cell),
            ])
        else:
            for a in avoid[:4]:
                ing_rows.append([
                    Paragraph("<b>Caution/Avoid</b>", ParagraphStyle(name="IngA", parent=table_cell_bold, textColor=colors.HexColor("#DC2626"))),
                    Paragraph(f"Review {_safe(a.get('item'))}: {_safe(a.get('reason'))}", table_cell),
                ])

        if ing_rows:
            story.append(
                Table(
                    ing_rows,
                    colWidths=[35 * mm, 139 * mm],
                    style=TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F8FAFC")),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("PADDING", (0, 0), (-1, -1), 4),
                        ]
                    ),
                )
            )
            story.append(Spacer(1, 3 * mm))

    # 8. Safety, Patch Testing & Limitations
    safety_items = document.get("safety_guidance", [])
    if safety_items:
        story.append(Paragraph("Safety & Application Guidance", section_heading))
        for item in safety_items:
            story.append(Paragraph(f"• {_safe(item)}", body_style))
        story.append(Spacer(1, 2 * mm))

    limitations = document.get("limitations", [])
    if limitations:
        story.append(Paragraph("Analysis Limitations", section_heading))
        for item in limitations:
            story.append(Paragraph(f"• {_safe(item)}", body_style))
        story.append(Spacer(1, 2 * mm))

    # Technical Transparency (Only included for technical export)
    if privacy_mode == "technical" or settings.report_pdf_include_technical_details:
        story.append(PageBreak())
        story.append(Paragraph("Technical Transparency & System Provenance", section_heading))
        story.append(Paragraph(f"Model versions: {_safe(str(document.get('model_versions', {})))}", body_style))
        story.append(Paragraph(f"Engine versions: {_safe(str(document.get('engine_versions', {})))}", body_style))
        story.append(Paragraph(f"Data freshness: {_safe(str(document.get('data_freshness', [])))}", body_style))
        story.append(Spacer(1, 4 * mm))

    # 9. Medical Disclaimer Box
    disclaimer_text = document.get(
        "medical_disclaimer",
        "DermaScan AI provides general skincare guidance based on visible facial characteristics and user-provided information. It is not a medical diagnostic system, does not prescribe treatment, and does not replace advice from a qualified dermatologist.",
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        Table(
            [
                [
                    Paragraph(f"<b>CLINICAL NOTICE:</b> {_safe(disclaimer_text)} Seek professional advice for severe, painful, infected, persistent, rapidly changing, or unusual skin concerns.", disclaimer_style)
                ]
            ],
            colWidths=[174 * mm],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )
    )

    try:
        doc = SimpleDocTemplate(
            str(target),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=18 * mm,
            title=report_title,
            author="DermaScan AI",
            pageCompression=0,
        )

        def callback(canvas, report_doc):
            _footer(canvas, report_doc, report_id, version)

        doc.build(story, onFirstPage=callback, onLaterPages=callback)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise ReportExportError("PDF rendering failed.") from exc

    return ExportedPdf(
        physical_path=target,
        download_filename=f"DermaScan-{report_id}-v{version}.pdf",
    )

