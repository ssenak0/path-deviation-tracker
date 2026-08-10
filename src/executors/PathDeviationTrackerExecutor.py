"""NovaVision capsule executor."""

import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "../../../../"))

from sdks.novavision.src.base.component import Capsule
from sdks.novavision.src.helper.executor import Executor
from sdks.novavision.src.base.model import Image

from novavision.path_deviation_tracker.models.PackageModel import PackageModel
from novavision.path_deviation_tracker.utils.engine import PathDeviationService, ValidationError
from novavision.path_deviation_tracker.utils.response import build_response


class PathDeviationTrackerExecutor(Capsule):
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
    def _get_video_identifier(image) -> str:
        """Video Feed Image nesnesinden video_metadata.video_identifier değerini alır."""
        current = image
        # SDK nesnesi, Pydantic model veya JSON/dict taşıma biçimini destekler.
        for _ in range(3):
            if isinstance(current, dict):
                metadata = current.get("video_metadata") or current.get("videoMetadata")
                if metadata:
                    identifier = metadata.get("video_identifier") or metadata.get("videoIdentifier")
                    if identifier:
                        return str(identifier)
                current = current.get("value")
            else:
                metadata = getattr(current, "video_metadata", None) or getattr(current, "videoMetadata", None)
                if metadata:
                    identifier = getattr(metadata, "video_identifier", None) or getattr(metadata, "videoIdentifier", None)
                    if identifier:
                        return str(identifier)
                current = getattr(current, "value", None)
            if current is None:
                break
        raise ValidationError("Video Feed inputImage içinde video_metadata.video_identifier bulunamadı.")

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
        video_id = self._get_video_identifier(self.image)
        
        # Hocanın standart mimarisine uyum sağlamak ve pipeline senkronizasyonunu 
        # tetiklemek için resmi Redis üzerinden geçiriyoruz.
        if self.image:
            img = Image.get_frame(img=self.image, redis_db=self.redis_db)
            self.image = Image.set_frame(img=img, package_uID=self.uID, redis_db=self.redis_db)

        detections = [self._to_dict(item) for item in self.detections] if self.detections else []
        
        self.output_detections = self.service.process_frame(
            video_id=video_id,
            detections=detections,
            reference_path=self.reference_path,
            triggering_anchor=self.triggering_anchor,
        )
        return build_response(self)


if __name__ == "__main__":
    Executor(sys.argv[1]).run()
