from threading import RLock
from typing import Any, Callable

from app.core.config import Settings
from app.core.skin_concern_labels import CONCERN_DISPLAY_NAMES, CONCERN_LABELS
from app.ml.skin_concern_model_loader import (
    ConcernModelLoadError,
    ConcernModelUnavailableError,
    SkinConcernModelBundle,
    load_skin_concern_model_bundle,
)


class SkinConcernModelRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._bundle: SkinConcernModelBundle | None = None
        self._error_code = "not_initialized"

    def initialize(
        self, settings: Settings, load_function: Callable[[Any], Any] | None = None
    ) -> None:
        with self._lock:
            if settings.ai_demo_mode:
                from app.ml.demo_models import create_demo_concern_bundle

                self._bundle = create_demo_concern_bundle(settings)
                self._error_code = ""
                return
            try:
                self._bundle = load_skin_concern_model_bundle(settings, load_function)
                self._error_code = ""
            except ConcernModelUnavailableError:
                self._bundle = None
                self._error_code = "model_artifacts_unavailable"
            except ConcernModelLoadError:
                self._bundle = None
                self._error_code = "model_load_failed"

    def set_bundle_for_testing(self, bundle: SkinConcernModelBundle | None) -> None:
        with self._lock:
            self._bundle = bundle
            self._error_code = "" if bundle else "model_artifacts_unavailable"

    def require_bundle(self) -> SkinConcernModelBundle:
        with self._lock:
            if self._bundle is None:
                raise ConcernModelUnavailableError
            return self._bundle

    def status(self) -> dict[str, Any]:
        with self._lock:
            if self._bundle is None:
                return {"loaded": False, "reason": self._error_code}
            return {
                "loaded": True,
                "mode": self._bundle.metadata.get("analysis_mode", "model"),
                "model_name": self._bundle.metadata["model_name"],
                "model_version": self._bundle.metadata["model_version"],
                "number_of_labels": len(CONCERN_LABELS),
                "thresholds_calibrated": self._bundle.thresholds_calibrated,
                "supported_observations": [
                    CONCERN_DISPLAY_NAMES[label] for label in CONCERN_LABELS
                ],
            }


skin_concern_model_registry = SkinConcernModelRegistry()


def get_skin_concern_model_registry() -> SkinConcernModelRegistry:
    return skin_concern_model_registry
