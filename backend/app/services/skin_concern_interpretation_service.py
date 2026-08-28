from dataclasses import dataclass

from app.core.config import Settings
from app.core.skin_concern_labels import CONCERN_DISPLAY_NAMES
from app.services.skin_concern_fusion_service import QuestionnaireComparison

OBSERVED_EXPLANATIONS = {
    "visible_oiliness": "Visible shine-like characteristics were observed in the available facial image.",
    "dry_looking_areas": "Some areas showed dry-looking or matte textural characteristics.",
    "visible_pores": "Pore-like texture was visibly noticeable in the available facial image.",
    "visible_redness": "Some areas appeared redder than surrounding skin.",
    "uneven_looking_tone": "Mild variation in visible facial colour or brightness was observed.",
    "dark_spots": "Localized darker-looking spots were observed relative to nearby skin.",
    "acne_like_spots": "Visible acne-like spot characteristics were observed without making a medical diagnosis.",
    "under_eye_darkness": "Darker-looking characteristics were observed in the general under-eye appearance.",
    "dull_looking_appearance": "The image showed a lower-radiance or dull-looking overall appearance.",
    "fine_line_visibility": "Small line-like textures were visible in the available facial image.",
}

CONCERN_LIMITATIONS = {
    "visible_oiliness": ["Lighting and flash can affect visible shine."],
    "dry_looking_areas": ["Image texture cannot confirm skin hydration or a medical condition."],
    "visible_pores": ["Camera sharpness and distance can affect pore visibility."],
    "visible_redness": ["Lighting and colour balance can affect visible redness."],
    "uneven_looking_tone": ["Shadows and white balance can affect visible tone variation."],
    "dark_spots": ["This observation does not identify the cause of a darker-looking spot."],
    "acne_like_spots": ["Spot-like appearance is not a clinical acne diagnosis."],
    "under_eye_darkness": [
        "Lighting and natural facial structure can affect under-eye appearance."
    ],
    "dull_looking_appearance": ["Overall brightness and contrast can affect visible radiance."],
    "fine_line_visibility": ["Fine-line visibility does not determine age or a medical condition."],
}


@dataclass(frozen=True)
class InterpretedConcern:
    concern_code: str
    display_name: str
    score: float
    threshold: float
    status: str
    visible_severity: str
    regions: list[str]
    explanation: str
    questionnaire_agreement: str
    questionnaire_reported_value: str | None
    questionnaire_explanation: str
    limitations: list[str]


def visible_severity(
    score: float,
    threshold: float,
    settings: Settings,
    *,
    calibrated: bool,
) -> str:
    if not calibrated or score <= threshold:
        return "uncertain"
    distance = (score - threshold) / max(1e-9, 1.0 - threshold)
    if distance < settings.concern_moderate_severity_distance:
        return "mild"
    if distance < settings.concern_prominent_severity_distance:
        return "moderate"
    return "prominent"


def interpret_concern(
    *,
    concern_code: str,
    score: float,
    threshold: float,
    comparison: QuestionnaireComparison,
    regions: list[str],
    settings: Settings,
    thresholds_calibrated: bool,
) -> InterpretedConcern:
    difference = score - threshold
    if difference >= settings.concern_uncertainty_margin:
        status = "observed"
    elif difference <= -settings.concern_uncertainty_margin:
        status = "not_observed"
    elif comparison.agreement == "Strong" and difference >= 0:
        status = "possible"
    else:
        status = "uncertain"

    severity = (
        visible_severity(score, threshold, settings, calibrated=thresholds_calibrated)
        if status == "observed"
        else "uncertain"
    )
    if status == "observed":
        explanation = OBSERVED_EXPLANATIONS[concern_code]
    elif status == "possible":
        explanation = (
            "The model score was close to its decision threshold, while relevant "
            "self-reported behavior provided limited supporting context."
        )
    elif status == "uncertain":
        explanation = (
            "The model score was close to its decision threshold, so no definite "
            "visual observation was made."
        )
    else:
        explanation = "This visible characteristic was not clearly observed."
    return InterpretedConcern(
        concern_code=concern_code,
        display_name=CONCERN_DISPLAY_NAMES[concern_code],
        score=score,
        threshold=threshold,
        status=status,
        visible_severity=severity,
        regions=regions if status in {"observed", "possible"} else [],
        explanation=explanation,
        questionnaire_agreement=comparison.agreement,
        questionnaire_reported_value=comparison.reported_value,
        questionnaire_explanation=comparison.explanation,
        limitations=CONCERN_LIMITATIONS[concern_code],
    )
