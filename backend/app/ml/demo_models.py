from __future__ import annotations

from typing import Any

import numpy as np

from app.core.config import Settings
from app.core.skin_concern_labels import CONCERN_LABELS
from app.ml.model_loader import EXPECTED_CLASSES, SkinTypeModelBundle
from app.ml.skin_concern_model_loader import SkinConcernModelBundle


class DeterministicSkinTypeDemoModel:
    """Deterministic mock for demonstrations; it is not a trained classifier."""

    def predict(self, tensor: Any, verbose: int = 0) -> np.ndarray:
        del verbose
        image = np.asarray(tensor, dtype=np.float64)[0]
        brightness = float(image.mean())
        channel_spread = float(np.ptp(image.mean(axis=(0, 1))))
        if brightness < 0.38:
            values = [0.16, 0.10, 0.58, 0.16]
        elif brightness > 0.68:
            values = [0.13, 0.58, 0.10, 0.19]
        elif channel_spread > 0.10:
            values = [0.20, 0.22, 0.18, 0.40]
        else:
            values = [0.55, 0.16, 0.15, 0.14]
        return np.asarray([values], dtype=np.float32)


class DeterministicConcernDemoModel:
    """Image-statistic mock used only when AI_DEMO_MODE is explicitly enabled."""

    def predict(self, tensor: Any, verbose: int = 0) -> np.ndarray:
        del verbose
        image = np.asarray(tensor, dtype=np.float64)[0]
        brightness = float(image.mean())
        contrast = float(image.std())
        red_bias = float(image[..., 0].mean() - image[..., 1].mean())
        scores = np.asarray(
            [
                0.58 if brightness > 0.62 else 0.28,
                0.58 if brightness < 0.42 else 0.30,
                min(0.70, 0.25 + contrast),
                min(0.72, max(0.20, 0.42 + red_bias)),
                min(0.65, 0.28 + contrast * 0.8),
                0.34,
                min(0.62, 0.26 + contrast * 0.7),
                0.38,
                0.52 if brightness < 0.48 else 0.30,
                min(0.55, 0.25 + contrast * 0.5),
            ],
            dtype=np.float32,
        )
        return scores.reshape(1, len(CONCERN_LABELS))


def create_demo_skin_type_bundle(settings: Settings) -> SkinTypeModelBundle:
    metadata = {
        "model_name": "DermaScan Deterministic Demonstration",
        "model_version": "demo-v1",
        "analysis_mode": "demonstration",
        "input_width": settings.model_input_width,
        "input_height": settings.model_input_height,
        "input_channels": settings.model_input_channels,
    }
    return SkinTypeModelBundle(
        model=DeterministicSkinTypeDemoModel(),
        metadata=metadata,
        class_map={index: label for index, label in enumerate(EXPECTED_CLASSES)},
    )


def create_demo_concern_bundle(settings: Settings) -> SkinConcernModelBundle:
    del settings
    thresholds = {label: 0.50 for label in CONCERN_LABELS}
    return SkinConcernModelBundle(
        model=DeterministicConcernDemoModel(),
        metadata={
            "model_name": "DermaScan Deterministic Concern Demonstration",
            "model_version": "demo-v1",
            "analysis_mode": "demonstration",
        },
        label_map={index: label for index, label in enumerate(CONCERN_LABELS)},
        thresholds=thresholds,
        thresholds_calibrated=False,
    )
