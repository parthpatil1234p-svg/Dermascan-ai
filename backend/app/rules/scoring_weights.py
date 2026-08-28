from app.core.config import Settings

SCORING_CONFIGURATION_VERSION = "1.0.0"


def get_scoring_weights(settings: Settings) -> dict[str, float]:
    weights = settings.recommendation_weights
    if any(value < 0 or value > 1 for value in weights.values()):
        raise ValueError("Recommendation weights must be between zero and one.")
    if abs(sum(weights.values()) - 1.0) > 1e-6:
        raise ValueError("Recommendation weights must total 1.0.")
    return weights
