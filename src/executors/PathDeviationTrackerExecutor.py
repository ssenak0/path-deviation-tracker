"""NovaVision capsule executor."""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from sdks.novavision.src.base.component import Component
from sdks.novavision.src.helper.executor import Executor
from sdks.novavision.src.base.model import Image

sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from src.models.PackageModel import PackageModel
from src.utils.engine import PathDeviationService, ValidationError
from src.utils.response import build_response


class PathDeviationTrackerExecutor(Component):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**self.request.data)
        self.image = self.request.get_param("inputImage")
        self.detections = self.request.get_param("detections")
        roi_str = self.request.get_param("referenceRoi")
        
        # Dinamik ölçekleme için videonun gerçek çözünürlüğünü bulalım
        video_w, video_h = 1920, 1080
        if self.image:
            img_obj = self.image[0] if isinstance(self.image, list) else self.image
            if hasattr(img_obj, "metadata") and img_obj.metadata:
                video_w = float(img_obj.metadata.get("width", 1920))
                video_h = float(img_obj.metadata.get("height", 1080))
        
        self.reference_path = self._parse_reference_roi(roi_str, video_w, video_h)
        self.triggering_anchor = self.request.get_param("triggeringAnchor") or "CENTER"
        self.service = PathDeviationService()

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    @staticmethod
    def _parse_reference_roi(value, video_w=1920.0, video_h=1080.0):
        if not value:
            return [[0,0], [0,1]] # default fallback
        try:
            import re
            
            # 1. Tuval (Canvas) boyutunu bul
            canvas_w, canvas_h = video_w, video_h
            canvas_match = re.search(r'canvasSize\s*:\s*\{\s*width\s*:\s*(\d+)\s*,\s*height\s*:\s*(\d+)\s*\}', value)
            if canvas_match:
                canvas_w = float(canvas_match.group(1))
                canvas_h = float(canvas_match.group(2))
                
            # 2. X ve Y eksenleri için Oto-Ölçekleme katsayılarını hesapla
            scale_x = video_w / canvas_w if canvas_w else 1.0
            scale_y = video_h / canvas_h if canvas_h else 1.0

            # 3. Çizilen tüm noktaları (polygon/polyline) bul
            points_matches = re.findall(r'points\s*:\s*\[([\d,\.\s]+)\]', value)
            if points_matches:
                # En son çizilen şekli (phantom coordinate'leri aşmak için) kullanıyoruz
                last_points_str = points_matches[-1]
                coords = [float(x.strip()) for x in last_points_str.split(',') if x.strip()]
                
                # 4. Koordinatları otomatik oranlayarak (scale_x ve scale_y) kaydet!
                if len(coords) >= 4:
                    return [[coords[i] * scale_x, coords[i+1] * scale_y] for i in range(0, len(coords), 2)]
                    
        except Exception as error:
            pass
        return [[0,0], [0,1]]

    @staticmethod
    def _to_dict(detection):
        if isinstance(detection, dict):
            return detection
        if hasattr(detection, "dict"):
            return detection.dict()
        if hasattr(detection, "model_dump"):
            return detection.model_dump()
        raise ValidationError("detections içindeki öğeler dict veya Nova Detection nesnesi olmalıdır.")

    def run(self):
        # Tek bir sabit videomuz olduğu için metadata araması yapmıyoruz.
        video_id = "default_video"
        

        detections = [self._to_dict(item) for item in self.detections] if self.detections else []
        
        self.output_detections = self.service.process_frame(
            video_id=video_id,
            detections=detections,
            reference_path=self.reference_path,
            triggering_anchor=self.triggering_anchor,
        )
        packageModel = build_response(context=self)
        return packageModel


if __name__ == "__main__":
    Executor(sys.argv[1]).run()
