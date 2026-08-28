from threading import RLock
from typing import Any, Callable

from app.core.config import Settings
from app.ml.model_loader import (
    ModelLoadError,
    ModelUnavailableError,
    SkinTypeModelBundle,
    load_skin_type_model_bundle,
)


class SkinTypeModelRegistry:
    def __init__(self) -> None:
        self._lock = RLock()
        self._bundle: SkinTypeModelBundle | None = None
        self._error_code = "not_initialized"

    def initialize(
        self,
        settings: Settings,
        load_function: Callable[[Any], Any] | None = None,
    ) -> None:
        with self._lock:
            if settings.ai_demo_mode:
                from app.ml.demo_models import create_demo_skin_type_bundle

                self._bundle = create_demo_skin_type_bundle(settings)
                self._error_code = ""
                return
            try:
                self._bundle = load_skin_type_model_bundle(settings, load_function)
                self._error_code = ""
            except ModelUnavailableError:
                self._bundle = None
                self._error_code = "model_artifacts_unavailable"
            except ModelLoadError:
                self._bundle = None
                self._error_code = "model_load_failed"

    def set_bundle_for_testing(self, bundle: SkinTypeModelBundle | None) -> None:
        with self._lock:
            self._bundle = bundle
            self._error_code = "" if bundle else "model_artifacts_unavailable"

    def require_bundle(self) -> SkinTypeModelBundle:
        with self._lock:
            if self._bundle is None:
                raise ModelUnavailableError
            return self._bundle

    def status(self) -> dict[str, Any]:
        with self._lock:
            if self._bundle is None:
                return {"loaded": False, "reason": self._error_code}
            metadata = self._bundle.metadata
            return {
                "loaded": True,
                "mode": metadata.get("analysis_mode", "model"),
                "model_name": metadata["model_name"],
                "model_version": metadata["model_version"],
                "input_size": [
                    metadata["input_width"],
                    metadata["input_height"],
                    metadata["input_channels"],
                ],
                "classes": [label.title() for label in EXPECTED_CLASS_NAMES],
            }


EXPECTED_CLASS_NAMES = ("normal", "oily", "dry", "combination")
skin_type_model_registry = SkinTypeModelRegistry()


def get_skin_type_model_registry() -> SkinTypeModelRegistry:
    return skin_type_model_registry
