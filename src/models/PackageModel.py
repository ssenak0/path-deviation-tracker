"""NovaVision Package Model Şartnamesine uygun capsule tanımı."""

from typing import List, Literal, Optional, Union
from pydantic import Field, validator
from sdks.novavision.src.base.model import Config, Configs, Image, Input, Inputs, Output, Outputs, Package, Request, Response, Model


class InputImage(Input):
    name: Literal["inputImage"] = "inputImage"
    value: Union[List[Image], Image]
    type: str = "object"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        val = values.get('value')
        if isinstance(val, Image):
            return "object"
        elif isinstance(val, list):
            return "list"
        return "object"

    class Config:
        title = "Image"


class BoundingBox(Model):
    left: float
    top: float
    width: float
    height: float


class Detection(Model):
    boundingBox: Optional[BoundingBox] = None
    confidence: Optional[float] = None
    classLabel: Optional[str] = None
    classId: Optional[int] = None
    tracker_id: Optional[Union[str, int]] = None
    metadata: Optional[dict] = None


class InputDetections(Input):
    name: Literal["detections"] = "detections"
    value: Union[List[Detection], Detection]
    type: str = "object"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        val = values.get('value')
        if isinstance(val, Detection):
            return "object"
        elif isinstance(val, list):
            return "list"
        return "object"

    class Config:
        title = "Detections"


class ConfigAnchorCenter(Config):
    name: Literal["CENTER"] = "CENTER"
    value: Literal["CENTER"] = "CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Center"


class ConfigAnchorBottomCenter(Config):
    name: Literal["BOTTOM_CENTER"] = "BOTTOM_CENTER"
    value: Literal["BOTTOM_CENTER"] = "BOTTOM_CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Bottom Center"


class ConfigAnchorTopCenter(Config):
    name: Literal["TOP_CENTER"] = "TOP_CENTER"
    value: Literal["TOP_CENTER"] = "TOP_CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Top Center"


class ConfigTriggeringAnchor(Config):
    name: Literal["triggeringAnchor"] = "triggeringAnchor"
    value: Union[ConfigAnchorCenter, ConfigAnchorBottomCenter, ConfigAnchorTopCenter]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"
    class Config:
        title = "Tracking Anchor"


class ConfigReferencePath(Config):
    name: Literal["referencePath"] = "referencePath"
    value: str = Field(default="[[100, 200], [200, 300]]")
    type: Literal["string"] = "string"
    field: Literal["textInput"] = "textInput"
    class Config:
        title = "Reference Path ([x, y] JSON)"


class PathDeviationInputs(Inputs):
    inputImage: InputImage
    detections: InputDetections


class PathDeviationConfigs(Configs):
    referencePath: ConfigReferencePath
    triggeringAnchor: ConfigTriggeringAnchor


class OutputDetections(Output):
    name: Literal["outputDetections"] = "outputDetections"
    value: Union[List[Detection], Detection]
    type: str = "object"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        val = values.get('value')
        if isinstance(val, Detection):
            return "object"
        elif isinstance(val, list):
            return "list"
        return "object"

    class Config:
        title = "Detections/ROI"


class PathDeviationOutputs(Outputs):
    outputDetections: OutputDetections


class PathDeviationTrackerExecutorRequest(Request):
    inputs: Optional[PathDeviationInputs]
    configs: PathDeviationConfigs
    class Config:
        json_schema_extra = {"target": "configs"}


class PathDeviationTrackerExecutorResponse(Response):
    outputs: PathDeviationOutputs


class PathDeviationTrackerExecutor(Config):
    name: Literal["PathDeviationTrackerExecutor"] = "PathDeviationTrackerExecutor"
    value: Union[PathDeviationTrackerExecutorRequest, PathDeviationTrackerExecutorResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"
    class Config:
        title = "Path Deviation"
        json_schema_extra = {"target": {"value": 0}}


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: Union[PathDeviationTrackerExecutor]
    type: Literal["executor"] = "executor"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"
    class Config:
        title = "Task"
        json_schema_extra = {
            "target": "value"
        }


class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["capsule"] = "capsule"
    name: Literal["PathDeviationTracker"] = "PathDeviationTracker"
