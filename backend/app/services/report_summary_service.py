from typing import Any


def generate_executive_summary(
    skin_type: dict[str, Any] | None,
    concerns: dict[str, Any] | None,
    profile: dict[str, Any] | None,
    *,
    incomplete: bool = False,
) -> str:
    if incomplete:
        return "This report is incomplete because one or more required workflow sections are unavailable. No missing result has been inferred."
    skin = (skin_type or {}).get("final_skin_type", "Uncertain")
    confidence = str((skin_type or {}).get("confidence_level", "low")).title()
    observed = [
        item.get("display_name", item.get("concern_code", "visible characteristic")).lower()
        for item in (concerns or {}).get("concern_results", [])
        if item.get("status") == "observed"
    ]
    observation_text = (
        f" Visible observations included {', '.join(observed[:3])}."
        if observed
        else " No visible observation was represented as certain."
    )
    sensitivity = (profile or {}).get("is_sensitive")
    sensitivity_text = (
        " Self-reported sensitivity was recorded and remains separate from image observations."
        if sensitivity is not None
        else " Sensitivity was not specified."
    )
    return f"The analysis suggests {skin.lower()} skin with {confidence.lower()} confidence.{observation_text}{sensitivity_text} Recommendations and routines are general guidance from the available catalogue."
