"""Üretim için yol sapması (discrete Fréchet distance) çekirdeği.

Bu modül NovaVision SDK'ya bağlı değildir. Böylece servis/worker içinde aynı kod
test edilebilir; executor yalnızca platform isteğini bu modülün girdisine çevirir.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from threading import RLock
from time import time
from typing import Dict, List, Mapping, Protocol, Sequence, Tuple

Point = Tuple[float, float]


class ValidationError(ValueError):
    """İstek sözleşmesine uymayan veriler için güvenli hata."""


class PathStore(Protocol):
    def get(self, key: str) -> dict | None: ...
    def set(self, key: str, value: dict) -> None: ...
    def delete(self, key: str) -> None: ...


class InMemoryPathStore:
    """Tek worker veya geliştirme ortamı için thread-safe durum deposu."""

    def __init__(self) -> None:
        self._items: Dict[str, dict] = {}
        self._lock = RLock()

    def get(self, key: str) -> dict | None:
        with self._lock:
            value = self._items.get(key)
            return None if value is None else {**value, "points": list(value["points"])}

    def set(self, key: str, value: dict) -> None:
        with self._lock:
            self._items[key] = {**value, "points": list(value["points"])}

    def delete(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)


@dataclass(frozen=True)
class PathDeviationSettings:
    max_history_points: int = 300
    state_ttl_seconds: int = 3600

    def __post_init__(self) -> None:
        if self.max_history_points < 2:
            raise ValueError("max_history_points en az 2 olmalıdır.")


def discrete_frechet_distance(path_a: Sequence[Point], path_b: Sequence[Point]) -> float:
    """Sıralamayı koruyan iki rota arasındaki discrete Fréchet uzaklığı."""
    if not path_a or not path_b:
        raise ValidationError("Karşılaştırılan iki rota da boş olamaz.")
    previous = [0.0] * len(path_b)
    for i, first in enumerate(path_a):
        current = [0.0] * len(path_b)
        for j, second in enumerate(path_b):
            distance = hypot(first[0] - second[0], first[1] - second[1])
            if i == 0 and j == 0:
                current[j] = distance
            elif i == 0:
                current[j] = max(current[j - 1], distance)
            elif j == 0:
                current[j] = max(previous[j], distance)
            else:
                current[j] = max(min(previous[j], previous[j - 1], current[j - 1]), distance)
        previous = current
    return previous[-1]


class PathDeviationService:
    """Video ve tracker kimliğine göre rotayı saklar, tespitleri zenginleştirir."""

    def __init__(self, store: PathStore | None = None, settings: PathDeviationSettings | None = None) -> None:
        self.store = store or InMemoryPathStore()
        self.settings = settings or PathDeviationSettings()

    def process_frame(self, video_id: str, detections: Sequence[Mapping[str, object]], reference_path: Sequence[Sequence[float]], triggering_anchor: str = "CENTER") -> List[dict]:
        if not isinstance(video_id, str) or not video_id.strip():
            raise ValidationError("video_id zorunlu bir metindir.")
        reference = self._validate_path(reference_path)
        now = time()
        output: List[dict] = []
        for detection in detections:
            tracker_id = detection.get("trackerID") or detection.get("tracker_id")
            if tracker_id is None or str(tracker_id).strip() == "":
                raise ValidationError("Her detection için tracker_id veya trackerID zorunludur.")
            point = self._extract_anchor(detection, triggering_anchor)
            key = f"path-deviation:{video_id}:{tracker_id}"
            state = self.store.get(key) or {"points": [], "updated_at": now}
            points = [] if now - float(state["updated_at"]) > self.settings.state_ttl_seconds else state["points"]
            points.append(point)
            points = points[-self.settings.max_history_points:]
            self.store.set(key, {"points": points, "updated_at": now})
            enriched = dict(detection)
            deviation = round(discrete_frechet_distance(points, reference), 2)
            # Roboflow Path Deviation ile aynı şekilde, değeri detection metadata'sına ekle.
            metadata = dict(enriched.get("metadata") or {})
            metadata["path_deviation"] = deviation
            metadata["path_points"] = len(points)
            enriched["metadata"] = metadata
            output.append(enriched)
        return output

    @staticmethod
    def _extract_anchor(detection: Mapping[str, object], anchor: str) -> Point:
        if "x" in detection and "y" in detection and anchor == "CENTER":
            return float(detection["x"]), float(detection["y"])
            
        bbox = detection.get("boundingBox", detection)
        if not isinstance(bbox, Mapping):
            if hasattr(bbox, "dict"):
                bbox = bbox.dict()
            elif hasattr(bbox, "model_dump"):
                bbox = bbox.model_dump()
            else:
                bbox = detection

        required = ("left", "top", "width", "height")
        if all(name in bbox for name in required):
            center_x = float(bbox["left"]) + float(bbox["width"]) / 2
            top, height = float(bbox["top"]), float(bbox["height"])
            anchors = {"CENTER": (center_x, top + height / 2), "TOP_CENTER": (center_x, top), "BOTTOM_CENTER": (center_x, top + height)}
            if anchor in anchors:
                return anchors[anchor]
        raise ValidationError("Detection seçilen anchor için gerekli koordinatları içermelidir.")

    @staticmethod
    def _validate_path(points: Sequence[Sequence[float]]) -> List[Point]:
        if not isinstance(points, Sequence) or len(points) < 2:
            raise ValidationError("reference_path en az iki [x, y] noktası içermelidir.")
        try:
            return [(float(point[0]), float(point[1])) for point in points]
        except (IndexError, TypeError, ValueError) as error:
            raise ValidationError("Her reference_path noktası [x, y] olmalıdır.") from error
