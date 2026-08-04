import json
import numpy as np
from typing import List, Tuple, Union, Any


class PathDeviationEngine:

    @staticmethod
    def euclidean_distance(point1: Any, point2: Any) -> float:
        return float(np.linalg.norm(point1 - point2))

    @classmethod
    def calculate_frechet_distance(
        cls, path1: Union[np.ndarray, list, tuple], 
        path2: Union[np.ndarray, list, tuple]
    ) -> float:
        p1 = np.array(path1, dtype=np.float64)
        p2 = np.array(path2, dtype=np.float64)

        n = len(p1)
        m = len(p2)

        if n == 0 or m == 0:
            return 0.0

        ca = np.zeros((n, m), dtype=np.float64)
        ca[0, 0] = cls.euclidean_distance(p1[0], p2[0])

        for i in range(1, n):
            ca[i, 0] = max(ca[i - 1, 0], cls.euclidean_distance(p1[i], p2[0]))

        for j in range(1, m):
            ca[0, j] = max(ca[0, j - 1], cls.euclidean_distance(p1[0], p2[j]))

        for i in range(1, n):
            for j in range(1, m):
                min_previous_cost = min(ca[i - 1, j], ca[i, j - 1], ca[i - 1, j - 1])
                current_point_cost = cls.euclidean_distance(p1[i], p2[j])
                ca[i, j] = max(min_previous_cost, current_point_cost)

        return float(ca[n - 1, m - 1])

    @staticmethod
    def extract_anchor_point(bbox: List[float], anchor_type: str = "CENTER") -> Tuple[float, float]:
        x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]
        width = x2 - x1
        height = y2 - y1

        anchor = anchor_type.upper()
        if anchor == "BOTTOM_CENTER":
            return (x1 + width / 2.0, float(y2))
        elif anchor == "TOP_CENTER":
            return (x1 + width / 2.0, float(y1))
        elif anchor == "CENTER_LEFT":
            return (float(x1), y1 + height / 2.0)
        elif anchor == "CENTER_RIGHT":
            return (float(x2), y1 + height / 2.0)
        else:
            return (x1 + width / 2.0, y1 + height / 2.0)

    @staticmethod
    def parse_reference_path(raw_path: Union[str, np.ndarray, list, tuple]) -> np.ndarray:
        if isinstance(raw_path, str):
            try:
                parsed_list = json.loads(raw_path)
                return np.array(parsed_list, dtype=np.float64)
            except Exception:
                return np.array([], dtype=np.float64)
        elif isinstance(raw_path, (list, tuple, np.ndarray)):
            return np.array(raw_path, dtype=np.float64)
        return np.array([], dtype=np.float64)
