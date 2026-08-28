from dataclasses import dataclass


@dataclass(frozen=True)
class QuestionnaireEvidence:
    oiliness_level: str
    dryness_level: str
    self_reported_sensitivity: bool | None


@dataclass(frozen=True)
class FusedSkinTypeResult:
    final_skin_type: str
    result_status: str
    agreement: str
    explanation: str
    issues: list[str]


def questionnaire_agrees(predicted_class: str, evidence: QuestionnaireEvidence) -> bool:
    oily = evidence.oiliness_level
    dry = evidence.dryness_level
    if predicted_class == "oily":
        return oily == "High" and dry in {"Low", "Moderate", "Not sure"}
    if predicted_class == "dry":
        return dry == "High" and oily in {"Low", "Moderate", "Not sure"}
    if predicted_class == "combination":
        return oily in {"Moderate", "High"} and dry in {"Moderate", "High"}
    return oily in {"Low", "Moderate", "Not sure"} and dry in {
        "Low",
        "Moderate",
        "Not sure",
    }


def questionnaire_strongly_conflicts(predicted_class: str, evidence: QuestionnaireEvidence) -> bool:
    oily = evidence.oiliness_level
    dry = evidence.dryness_level
    if predicted_class == "oily":
        return oily == "Low" and dry == "High"
    if predicted_class == "dry":
        return dry == "Low" and oily == "High"
    if predicted_class == "combination":
        return oily == "Low" and dry == "Low"
    return oily == "High" or dry == "High"


def fuse_skin_type_prediction(
    *,
    predicted_class: str,
    image_result_is_uncertain: bool,
    evidence: QuestionnaireEvidence,
) -> FusedSkinTypeResult:
    label = predicted_class.title()
    if image_result_is_uncertain:
        return FusedSkinTypeResult(
            final_skin_type="Uncertain",
            result_status="uncertain",
            agreement="Insufficient",
            explanation=(
                "The image prediction did not meet the configured confidence and "
                "separation thresholds, so no skin type was forced."
            ),
            issues=["MODEL_CONFIDENCE_INSUFFICIENT"],
        )
    if questionnaire_strongly_conflicts(predicted_class, evidence):
        return FusedSkinTypeResult(
            final_skin_type="Uncertain",
            result_status="uncertain",
            agreement="Conflict",
            explanation=(
                f"The image suggested {label.lower()} characteristics, but your "
                "questionnaire describes different skin behaviour."
            ),
            issues=["QUESTIONNAIRE_IMAGE_DISAGREEMENT"],
        )
    if questionnaire_agrees(predicted_class, evidence):
        return FusedSkinTypeResult(
            final_skin_type=label,
            result_status="estimated",
            agreement="Strong",
            explanation=(
                f"The visible image estimate and your questionnaire both suggest "
                f"{label.lower()} skin behaviour."
            ),
            issues=[],
        )
    return FusedSkinTypeResult(
        final_skin_type=label,
        result_status="estimated",
        agreement="Weak",
        explanation=(
            f"The image suggests {label.lower()} characteristics. Your questionnaire "
            "does not strongly confirm or contradict that estimate."
        ),
        issues=["QUESTIONNAIRE_EVIDENCE_MIXED"],
    )
