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
        self.reference_path = self._parse_reference_path(self.request.get_param("referencePath"))
        self.triggering_anchor = self.request.get_param("triggeringAnchor") or "CENTER"
        self.service = PathDeviationService()

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    @staticmethod
    def _parse_reference_path(value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError as error:
                raise ValidationError("referencePath geçerli JSON olmalıdır.") from error
        return value

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
