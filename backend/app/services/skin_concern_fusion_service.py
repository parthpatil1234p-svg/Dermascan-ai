from dataclasses import dataclass


@dataclass(frozen=True)
class ConcernQuestionnaireEvidence:
    oiliness_level: str
    dryness_level: str
    self_reported_sensitivity: bool | None


@dataclass(frozen=True)
class QuestionnaireComparison:
    agreement: str
    reported_value: str | None
    explanation: str


def compare_questionnaire(
    concern_code: str, evidence: ConcernQuestionnaireEvidence
) -> QuestionnaireComparison:
    if concern_code == "visible_oiliness":
        if evidence.oiliness_level == "High":
            return QuestionnaireComparison(
                "Strong",
                "High oiliness",
                "Your questionnaire also reports high oiliness.",
            )
        if evidence.oiliness_level == "Low":
            return QuestionnaireComparison(
                "Mixed",
                "Low oiliness",
                "Your questionnaire reports low oiliness, so the evidence is mixed.",
            )
        return QuestionnaireComparison(
            "Neutral",
            evidence.oiliness_level,
            "Your reported oiliness does not strongly confirm or contradict this score.",
        )
    if concern_code == "dry_looking_areas":
        if evidence.dryness_level == "High":
            return QuestionnaireComparison(
                "Strong",
                "High dryness",
                "Your questionnaire also reports high dryness.",
            )
        if evidence.dryness_level == "Low":
            return QuestionnaireComparison(
                "Mixed",
                "Low dryness",
                "Your questionnaire reports low dryness, so the evidence is mixed.",
            )
        return QuestionnaireComparison(
            "Neutral",
            evidence.dryness_level,
            "Your reported dryness does not strongly confirm or contradict this score.",
        )
    return QuestionnaireComparison(
        "Not Compared",
        None,
        "This visible characteristic is not inferred from questionnaire sensitivity, allergies, or notes.",
    )
