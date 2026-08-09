"""NovaVision Package Model Şartnamesine uygun capsule tanımı."""

from typing import List, Literal, Optional, Union

from pydantic import Field
from sdks.novavision.src.base.model import Config, Configs, Image, Input, Inputs, Output, Outputs, Package, Request, Response


class InputImage(Input):
    """Video Feed'den gelen, video metadata taşıyan güncel kare."""
    name: Literal["inputImage"] = "inputImage"
    value: Image
    type: Literal["Image"] = "Image"
    field: Literal["hiddenInput"] = "hiddenInput"

    class Config:
        title = "Image"


class InputDetections(Input):
    name: Literal["detections"] = "detections"
    value: List[dict]
    type: Literal["Detections"] = "Detections"
    field: Literal["hiddenInput"] = "hiddenInput"

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
        json_schema_extra = {"target": "value"}


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
    value: List[dict]
    type: Literal["Detections"] = "Detections"

    class Config:
        title = "Detections/ROI"


class PathDeviationOutputs(Outputs):
    outputDetections: OutputDetections


class PathDeviationRequest(Request):
    inputs: Optional[PathDeviationInputs]
    configs: PathDeviationConfigs
    class Config:
        json_schema_extra = {"target": "configs"}


class PathDeviationResponse(Response):
    outputs: PathDeviationOutputs


class PathDeviationTrackerExecutorConfig(Config):
    name: Literal["PathDeviationTrackerExecutor"] = "PathDeviationTrackerExecutor"
    value: Union[PathDeviationRequest, PathDeviationResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"
    class Config:
        title = "Path Deviation"
        json_schema_extra = {"target": {"value": 0}}


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: Union[PathDeviationTrackerExecutorConfig]
    type: Literal["executor"] = "executor"
    field: Literal["dependentDropdownlist"] = "dependentDropdownlist"
    class Config:
        title = "Task"


class PackageConfigs(Configs):
    executor: ConfigExecutor


class PackageModel(Package):
    configs: PackageConfigs
    type: Literal["capsule"] = "capsule"
    name: Literal["PathDeviationTracker"] = "PathDeviationTracker"
