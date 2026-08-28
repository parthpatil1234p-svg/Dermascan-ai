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
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0F766E"),
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=6,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["BodyText"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#475569"),
        )
    )
    story = [
        _paragraph(document["report_title"], styles["ReportTitle"]),
        _paragraph(
            f"Report ID: {document['final_report_id']} | Version: {document['report_version']} | Generated: {document['generated_at'].isoformat()}",
            styles["Small"],
        ),
        Spacer(1, 6 * mm),
        _paragraph("Important Disclaimer", styles["Section"]),
        _paragraph(document["medical_disclaimer"], styles["BodyText"]),
        _paragraph(
            "Seek professional advice for severe, painful, infected, persistent, rapidly changing, or unusual skin concerns.",
            styles["BodyText"],
        ),
        _paragraph("Executive Summary", styles["Section"]),
        _paragraph(document.get("summary", ""), styles["BodyText"]),
    ]
    profile = document.get("skin_profile_summary", {})
    if privacy_mode != "privacy_reduced" and settings.report_pdf_include_profile_details:
        story.extend(
            [
                _paragraph("User-Provided Skin Profile", styles["Section"]),
                Table(
                    [
                        ["Age group", _safe(profile.get("age_group"))],
                        ["Country", _safe(profile.get("country"))],
                        [
                            "Oiliness / dryness",
                            _safe(
                                f"{profile.get('oiliness_level')} / {profile.get('dryness_level')}"
                            ),
                        ],
                        [
                            "Self-reported sensitivity",
                            _safe(profile.get("self_reported_sensitivity")),
                        ],
                        [
                            "Known allergies",
                            _safe(", ".join(profile.get("known_allergies", [])) or "None reported"),
                        ],
                        [
                            "Ingredients to avoid",
                            _safe(
                                ", ".join(profile.get("ingredients_to_avoid", []))
                                or "None selected"
                            ),
                        ],
                    ],
                    colWidths=[48 * mm, 125 * mm],
                    style=TableStyle(
                        [
                            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("FONTSIZE", (0, 0), (-1, -1), 8),
                            ("LEADING", (0, 0), (-1, -1), 10),
                            ("PADDING", (0, 0), (-1, -1), 5),
                        ]
                    ),
                ),
            ]
        )
    skin = document.get("skin_type_summary", {})
    story.extend(
        [
            _paragraph("AI-Assisted Visible Results", styles["Section"]),
            _paragraph(
                f"Estimated skin type: {skin.get('skin_type', 'Unavailable')} | Confidence: {skin.get('confidence_level', 'Unavailable')} | Questionnaire agreement: {skin.get('questionnaire_agreement', 'Unavailable')}",
                styles["BodyText"],
            ),
        ]
    )
    observations = document.get("visible_concern_summary", {})
    for label in ("observed", "possible", "uncertain"):
        items = observations.get(label, [])
        if items:
            story.append(_paragraph(label.title(), styles["Heading3"]))
            for item in items:
                story.append(
                    _paragraph(
                        f"• {item.get('name')} - {item.get('visible_severity')} visible appearance; {', '.join(item.get('regions', []))}",
                        styles["BodyText"],
                    )
                )
    guidance = document.get("ingredient_guidance", {})
    story.append(_paragraph("Ingredient Guidance", styles["Section"]))
    for item in guidance.get("potentially_relevant", []):
        story.append(
            _paragraph(f"• {item.get('ingredient_role')}: {item.get('reason')}", styles["BodyText"])
        )
    if privacy_mode == "privacy_reduced":
        story.append(
            _paragraph(
                "Detailed allergy and avoidance guidance is hidden in this privacy-reduced export.",
                styles["BodyText"],
            )
        )
    else:
        for item in guidance.get("avoid_or_review", []):
            story.append(
                _paragraph(f"• Review {item.get('item')}: {item.get('reason')}", styles["BodyText"])
            )
    story.append(_paragraph("Rule-Based Product Recommendations", styles["Section"]))
    for item in document.get("product_recommendation_summary", []):
        price = item.get("price_at_report_time") or {}
        story.extend(
            [
                _paragraph(
                    f"{item.get('category', '').title()} #{item.get('rank')}: {item.get('product_name')} by {item.get('brand_name')}",
                    styles["Heading3"],
                ),
                _paragraph(
                    f"Relevance score: {item.get('score')}/100 ({item.get('score_band')}). {item.get('why_recommended')}",
                    styles["BodyText"],
                ),
                _paragraph(
                    f"Price recorded when generated: INR {price.get('amount', 'Unavailable')}. Availability: {item.get('availability_at_report_time')}",
                    styles["Small"],
                ),
            ]
        )
    for title, key in (("Morning Routine", "morning_routine"), ("Night Routine", "night_routine")):
        story.append(_paragraph(title, styles["Section"]))
        for step in document.get(key, []):
            optional = "Optional " if step.get("is_optional") else ""
            story.append(
                _paragraph(
                    f"{step.get('step_number')}. {optional}{step.get('category', '').title()}: {step.get('product_name')} - {step.get('usage_guidance')}",
                    styles["BodyText"],
                )
            )
    story.append(_paragraph("Safety Guidance", styles["Section"]))
    for item in document.get("safety_guidance", []):
        story.append(_paragraph(f"• {item}", styles["BodyText"]))
    story.append(_paragraph("Limitations", styles["Section"]))
    for item in document.get("limitations", []):
        story.append(_paragraph(f"• {item}", styles["BodyText"]))
    if privacy_mode == "technical" or settings.report_pdf_include_technical_details:
        story.extend(
            [
                PageBreak(),
                _paragraph("Technical Transparency", styles["Section"]),
                _paragraph(
                    f"Model versions: {document.get('model_versions', {})}", styles["BodyText"]
                ),
                _paragraph(
                    f"Engine versions: {document.get('engine_versions', {})}", styles["BodyText"]
                ),
                _paragraph(
                    f"Data freshness: {document.get('data_freshness', [])}", styles["BodyText"]
                ),
            ]
        )
    story.extend([Spacer(1, 8 * mm), _paragraph(document["medical_disclaimer"], styles["Small"])])
    try:
        doc = SimpleDocTemplate(
            str(target),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=20 * mm,
            title=document["report_title"],
            author="DermaScan AI",
            pageCompression=0,
        )

        def callback(canvas, report_doc):
            _footer(canvas, report_doc, document["final_report_id"], document["report_version"])

        doc.build(story, onFirstPage=callback, onLaterPages=callback)
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise ReportExportError("PDF rendering failed.") from exc
    return ExportedPdf(
        physical_path=target,
        download_filename=f"DermaScan-{document['final_report_id']}-v{document['report_version']}.pdf",
    )
