"""Frame analysis: MediaPipe for face counting, YOLOv8 for prohibited objects.

Models are loaded lazily so the API (and tests) start fast without the ML stack.
"""
import threading
from dataclasses import dataclass

from ..config import settings

PROHIBITED_LABELS = {"cell phone", "book", "laptop"}


@dataclass
class Finding:
    kind: str
    detail: str = ""


def findings_from_detections(face_count: int, labels: list[str]) -> list[Finding]:
    """Pure decision logic, kept separate from the models so it is unit-testable."""
    out: list[Finding] = []
    if face_count == 0:
        out.append(Finding("no_face", "No face visible"))
    elif face_count > 1:
        out.append(Finding("multiple_faces", f"{face_count} faces detected"))
    for label in sorted({l for l in labels if l in PROHIBITED_LABELS}):
        out.append(Finding("prohibited_object", label))
    return out


class FrameAnalyzer:
    def __init__(self) -> None:
        self._face = None
        self._yolo = None
        self._lock = threading.Lock()  # MediaPipe graphs are not thread-safe

    def _load(self) -> None:
        if self._face is None:
            import mediapipe as mp

            self._face = mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.6
            )
        if self._yolo is None:
            from ultralytics import YOLO

            self._yolo = YOLO(settings.yolo_model)

    def analyze(self, jpeg: bytes) -> list[Finding]:
        import cv2
        import numpy as np

        img = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return []
        with self._lock:
            self._load()
            faces = self._face.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).detections or []
            result = self._yolo(img, conf=settings.yolo_conf, verbose=False)[0]
        labels = [result.names[int(c)] for c in result.boxes.cls]
        return findings_from_detections(len(faces), labels)
