import os
import cv2
import sys
import json
import numpy as np

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

try:
    from sdks.novavision.src.media.image import Image
    from sdks.novavision.src.base.capsule import Capsule
    from sdks.novavision.src.helper.executor import Executor
except ImportError as e:
    raise ImportError(f"NovaVision import failed: {e}")

try:
    from capsules.PathDeviationTracker.src.models.PackageModel import PackageModel
    from capsules.PathDeviationTracker.src.utils.response import build_response
    from capsules.PathDeviationTracker.src.utils.engine import PathDeviationEngine
except ImportError:
    try:
        from capsules.Package.src.models.PackageModel import PackageModel
        from capsules.Package.src.utils.response import build_response
        from capsules.Package.src.utils.engine import PathDeviationEngine
    except ImportError:
        from src.models.PackageModel import PackageModel
        from src.utils.response import build_response
        from src.utils.engine import PathDeviationEngine


def unwrap_value(v, default=None):
    if v is None:
        return default
    if hasattr(v, "value"):
        return unwrap_value(v.value, default)
    if isinstance(v, dict) and "value" in v:
        return unwrap_value(v["value"], default)
    return v


def parse_bool(v, default=True):
    v = unwrap_value(v, default)
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in ("true", "1", "yes", "enable", "enabled")
    return bool(v) if v is not None else default


class PathDeviationExecutor(Capsule):
    def __init__(self, request, bootstrap):
        super().__init__(request, bootstrap)
        self.request.model = PackageModel(**(self.request.data if hasattr(self.request, "data") else {}))
        
        raw_anchor = self.request.get_param("ConfigTriggeringAnchor")
        if raw_anchor is None:
            raw_anchor = self.request.get_param("triggeringAnchor")
            
        raw_ref = self.request.get_param("ConfigReferencePath")
        if raw_ref is None:
            raw_ref = self.request.get_param("referencePath")
            
        raw_thresh = self.request.get_param("ConfigDeviationThreshold")
        if raw_thresh is None:
            raw_thresh = self.request.get_param("deviationThreshold")
            
        raw_draw = self.request.get_param("ConfigDrawBBox")
        if raw_draw is None:
            raw_draw = self.request.get_param("drawBBox")

        print("anchor raw:", raw_anchor)
        print("ref raw:", raw_ref)
        print("threshold raw:", raw_thresh)
        print("draw raw:", raw_draw)
        
        self.anchor_type = unwrap_value(raw_anchor, "CENTER")
        raw_ref_path = unwrap_value(raw_ref, "[[100, 200], [200, 300], [300, 400]]")
        self.deviation_threshold = float(unwrap_value(raw_thresh, 50.0))
        self.draw_bbox = parse_bool(raw_draw, True)
            
        self.image_input = self.request.get_param("inputImage")
        self.detections_input = self.request.get_param("inputDetections")
        
        self.reference_path = PathDeviationEngine.parse_reference_path(raw_ref_path)
        
        if not hasattr(self.__class__, "_trajectory_buffer"):
            self.__class__._trajectory_buffer = {}

    @staticmethod
    def bootstrap(config: dict) -> dict:
        return {}

    def _get_tracker_id(self, detect: dict, idx: int) -> str:
        if "trackerID" in detect and detect["trackerID"] is not None:
            return str(detect["trackerID"])
        elif "tracker_id" in detect and detect["tracker_id"] is not None:
            return str(detect["tracker_id"])
        elif "id" in detect and detect["id"] is not None:
            return str(detect["id"])
        else:
            return f"untracked_{idx}"

    def _get_video_id(self, detect: dict, img_obj) -> str:
        if "imgUID" in detect and detect["imgUID"]:
            return str(detect["imgUID"])
        elif "video_identifier" in detect and detect["video_identifier"]:
            return str(detect["video_identifier"])
        elif hasattr(img_obj, "video_identifier") and getattr(img_obj, "video_identifier"):
            return str(getattr(img_obj, "video_identifier"))
        elif hasattr(self, "uID") and self.uID:
            return str(self.uID)
        return "default_stream"

    def run(self):
        img_frame = Image.get_frame(img=self.image_input, redis_db=self.redis_db)
        
        target_obj = img_frame[0] if (isinstance(img_frame, list) and len(img_frame) > 0) else img_frame
        raw_image_data = getattr(target_obj, "value", target_obj)
        
        print("raw_image_data type:", type(raw_image_data))
        
        if isinstance(raw_image_data, bytes):
            arr = np.frombuffer(raw_image_data, dtype=np.uint8)
            raw_image_data = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        elif not isinstance(raw_image_data, np.ndarray) and raw_image_data is not None:
            try:
                raw_image_data = np.array(raw_image_data, dtype=np.uint8)
            except Exception:
                pass
                
        if raw_image_data is None or not isinstance(raw_image_data, np.ndarray) or raw_image_data.ndim < 2:
            raise ValueError(f"Invalid image input type: {type(raw_image_data)}")
            
        annotated_img = raw_image_data.copy()
        
        raw_detections = getattr(self.detections_input, "value", self.detections_input)
        print("DEBUG raw_detections type:", type(raw_detections))
        if isinstance(raw_detections, dict):
            if "value" in raw_detections and isinstance(raw_detections["value"], list):
                detections_list = raw_detections["value"]
            elif "detections" in raw_detections and isinstance(raw_detections["detections"], list):
                detections_list = raw_detections["detections"]
            else:
                detections_list = []
        elif isinstance(raw_detections, list):
            detections_list = raw_detections
        elif isinstance(raw_detections, str):
            try:
                parsed_json = json.loads(raw_detections)
                if isinstance(parsed_json, dict) and "value" in parsed_json:
                    detections_list = parsed_json["value"]
                elif isinstance(parsed_json, list):
                    detections_list = parsed_json
                else:
                    detections_list = []
            except Exception:
                detections_list = []
        else:
            detections_list = []

        print("detections_list len:", len(detections_list))
        output_detections = []
        
        if len(self.reference_path) > 1 and self.draw_bbox:
            pts = self.reference_path.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(annotated_img, [pts], isClosed=False, color=(255, 255, 0), thickness=2)

        for idx, detect in enumerate(detections_list):
            if not isinstance(detect, dict):
                continue
                
            bbox = [0.0, 0.0, 0.0, 0.0]
            target_dict = detect.get("value", detect.get("predictions", detect))
            if not isinstance(target_dict, dict):
                target_dict = detect

            if "boundingBox" in target_dict and isinstance(target_dict["boundingBox"], dict):
                box_dict = target_dict["boundingBox"]
                left = float(box_dict.get("left", 0.0))
                top = float(box_dict.get("top", 0.0))
                width = float(box_dict.get("width", 0.0))
                height = float(box_dict.get("height", 0.0))
                bbox = [left, top, left + width, top + height]
            elif "bbox" in target_dict and isinstance(target_dict["bbox"], (list, tuple)) and len(target_dict["bbox"]) == 4:
                bbox = [float(x) for x in target_dict["bbox"]]
            elif "box" in target_dict and isinstance(target_dict["box"], (list, tuple)) and len(target_dict["box"]) == 4:
                bbox = [float(x) for x in target_dict["box"]]
            elif all(k in target_dict for k in ("left", "top", "width", "height")):
                left = float(target_dict.get("left", 0.0))
                top = float(target_dict.get("top", 0.0))
                width = float(target_dict.get("width", 0.0))
                height = float(target_dict.get("height", 0.0))
                bbox = [left, top, left + width, top + height]
            elif all(k in target_dict for k in ("left", "top", "right", "bottom")):
                bbox = [float(target_dict["left"]), float(target_dict["top"]), float(target_dict["right"]), float(target_dict["bottom"])]
            elif all(k in target_dict for k in ("x", "y", "w", "h")):
                x = float(target_dict["x"])
                y = float(target_dict["y"])
                w = float(target_dict["w"])
                h = float(target_dict["h"])
                bbox = [x - w / 2.0, y - h / 2.0, x + w / 2.0, y + h / 2.0]
            else:
                print(f"DEBUG [PathDeviationTracker] - Skipping detection with unrecognized bbox format: {list(detect.keys())}")
                continue


            tracker_id = self._get_tracker_id(detect, idx)
            video_id = self._get_video_id(detect, img_frame)
            buffer_key = f"{video_id}_{tracker_id}"

            anchor_pt = PathDeviationEngine.extract_anchor_point(bbox, anchor_type=str(self.anchor_type))

            if buffer_key not in self.__class__._trajectory_buffer:
                self.__class__._trajectory_buffer[buffer_key] = []
                
            self.__class__._trajectory_buffer[buffer_key].append(anchor_pt)
            
            if len(self.__class__._trajectory_buffer[buffer_key]) > 1000:
                self.__class__._trajectory_buffer[buffer_key] = self.__class__._trajectory_buffer[buffer_key][-1000:]

            current_trajectory = self.__class__._trajectory_buffer[buffer_key]

            if len(self.reference_path) > 0 and len(current_trajectory) > 0:
                deviation_score = PathDeviationEngine.calculate_frechet_distance(current_trajectory, self.reference_path)
            else:
                deviation_score = 0.0

            is_deviated = bool(deviation_score > self.deviation_threshold)

            enriched_detect = dict(detect)
            if "tracker_id" in enriched_detect and "trackerID" not in enriched_detect:
                enriched_detect["trackerID"] = enriched_detect.pop("tracker_id")
            elif "tracker_id" in enriched_detect:
                enriched_detect.pop("tracker_id", None)
            enriched_detect["path_deviation"] = round(float(deviation_score), 2)
            enriched_detect["is_deviated"] = bool(is_deviated)
            output_detections.append(enriched_detect)

            if self.draw_bbox:
                x1, y1, x2, y2 = map(int, bbox)
                box_color = (0, 0, 255) if is_deviated else (0, 255, 0)
                cv2.rectangle(annotated_img, (x1, y1), (x2, y2), box_color, 2)
                
                label_text = f"ID:{tracker_id} Dev:{deviation_score:.1f}"
                cv2.putText(annotated_img, label_text, (x1, max(20, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

                if len(current_trajectory) > 1:
                    traj_pts = np.array(current_trajectory, dtype=np.int32).reshape((-1, 1, 2))
                    cv2.polylines(annotated_img, [traj_pts], isClosed=False, color=box_color, thickness=2)

        if hasattr(target_obj, "value"):
            target_obj.value = annotated_img
            self.output_annotated_image = Image.set_frame(img=img_frame, package_uID=self.uID, redis_db=self.redis_db)
        else:
            self.output_annotated_image = annotated_img

        self.output_path_deviation = output_detections
        self.image = self.output_annotated_image

        print("output_detections len:", len(output_detections))
        print("output_annotated_image type:", type(self.output_annotated_image))
        print("DEBUG output_path_deviation len:", len(self.output_path_deviation))

        package_model = build_response(context=self)
        return package_model


if "__main__" == __name__:
    arg = sys.argv[1] if len(sys.argv) > 1 else "default_test_arg"
    Executor(arg).run()
