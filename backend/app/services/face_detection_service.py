from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Protocol

import cv2
import numpy as np

from app.core.config import Settings
from app.utils.bounding_box import NormalizedBoundingBox


class FaceDetectorUnavailableError(Exception):
    pass


class FaceDetectorProcessingError(Exception):
    pass


@dataclass(frozen=True)
class DetectedFace:
    bounding_box: NormalizedBoundingBox
    confidence: float


class FaceDetector(Protocol):
    def detect(self, image: np.ndarray) -> list[DetectedFace]: ...


class MediaPipeFaceDetector:
    def __init__(self, *, min_confidence: float, max_faces: int) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise FaceDetectorUnavailableError("MediaPipe is not installed.") from exc

        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "face_detection"):
            raise FaceDetectorUnavailableError(
                "The installed MediaPipe package does not expose the Solutions face detector."
            )

        self._lock = threading.Lock()
        self._max_faces = max_faces
        self._detector = solutions.face_detection.FaceDetection(
            model_selection=1,
            min_detection_confidence=min_confidence,
        )

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        try:
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            with self._lock:
                result = self._detector.process(rgb_image)
        except Exception as exc:
            raise FaceDetectorProcessingError from exc

        detections = result.detections or []
        faces: list[DetectedFace] = []
        for detection in detections[: self._max_faces + 1]:
            relative_box = detection.location_data.relative_bounding_box
            faces.append(
                DetectedFace(
                    bounding_box=NormalizedBoundingBox(
                        x=float(relative_box.xmin),
                        y=float(relative_box.ymin),
                        width=float(relative_box.width),
                        height=float(relative_box.height),
                    ),
                    confidence=float(detection.score[0]) if detection.score else 0,
                )
            )
        return faces


class OpenCVHaarFaceDetector:
    def __init__(self) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(cascade_path)
        if self._cascade.empty():
            raise FaceDetectorUnavailableError("OpenCV Haar cascade is not available.")

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detections = self._cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(80, 80),
            )
        except Exception as exc:
            raise FaceDetectorProcessingError from exc

        image_height, image_width = image.shape[:2]
        faces: list[DetectedFace] = []
        for x, y, width, height in detections:
            faces.append(
                DetectedFace(
                    bounding_box=NormalizedBoundingBox(
                        x=float(x / image_width),
                        y=float(y / image_height),
                        width=float(width / image_width),
                        height=float(height / image_height),
                    ),
                    confidence=0.75,
                )
            )
        return faces


_detector_lock = threading.Lock()
_cached_detector: FaceDetector | None = None
_cached_signature: tuple[float, int] | None = None


def get_face_detector(settings: Settings) -> FaceDetector:
    global _cached_detector, _cached_signature
    signature = (
        settings.face_detection_min_confidence,
        settings.face_detection_max_faces,
    )
    with _detector_lock:
        if _cached_detector is not None and _cached_signature == signature:
            return _cached_detector

        try:
            detector: FaceDetector = MediaPipeFaceDetector(
                min_confidence=settings.face_detection_min_confidence,
                max_faces=settings.face_detection_max_faces,
            )
        except FaceDetectorUnavailableError:
            detector = OpenCVHaarFaceDetector()

        _cached_detector = detector
        _cached_signature = signature
        return detector
