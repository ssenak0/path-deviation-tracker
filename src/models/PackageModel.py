from typing import Optional, Union, List, Any
from typing_extensions import Literal
from pydantic import Field, validator

try:
    from sdks.novavision.src.base.model import (
        Package, Image, Inputs, Configs, Outputs, Response,
        Request, Config, Input, Output, Detections
    )
except ImportError:
    from pydantic import BaseModel
    class BaseStub(BaseModel):
        pass
    Package = Inputs = Configs = Outputs = Response = Request = Config = Input = Output = BaseStub
    Image = Any
    Detections = Any


class InputImage(Input):
    name: Literal["inputImage"] = "inputImage"
    value: Union[List[Image], Image]
    type: str = "object"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        val = values.get("value", value)
        if isinstance(val, list):
            return "list"
        return "object"

    class Config:
        title = "Image"


class InputDetections(Input):
    name: Literal["inputDetections"] = "inputDetections"
    value: Any
    type: str = "list"
    class Config:
        title = "Detections"


class OptionAnchorCenter(Config):
    name: Literal["Center"] = "Center"
    value: Literal["CENTER"] = "CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Center"


class OptionAnchorBottomCenter(Config):
    name: Literal["BottomCenter"] = "BottomCenter"
    value: Literal["BOTTOM_CENTER"] = "BOTTOM_CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Bottom Center"


class OptionAnchorTopCenter(Config):
    name: Literal["TopCenter"] = "TopCenter"
    value: Literal["TOP_CENTER"] = "TOP_CENTER"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Top Center"


class OptionAnchorCenterLeft(Config):
    name: Literal["CenterLeft"] = "CenterLeft"
    value: Literal["CENTER_LEFT"] = "CENTER_LEFT"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Center Left"


class OptionAnchorCenterRight(Config):
    name: Literal["CenterRight"] = "CenterRight"
    value: Literal["CENTER_RIGHT"] = "CENTER_RIGHT"
    type: Literal["string"] = "string"
    field: Literal["option"] = "option"
    class Config:
        title = "Center Right"


class ConfigDrawTrue(Config):
    name: Literal["True"] = "True"
    value: Literal[True] = True
    type: Literal["bool"] = "bool"
    field: Literal["option"] = "option"
    class Config:
        title = "Enable"


class ConfigDrawFalse(Config):
    name: Literal["False"] = "False"
    value: Literal[False] = False
    type: Literal["bool"] = "bool"
    field: Literal["option"] = "option"
    class Config:
        title = "Disable"


class ConfigTriggeringAnchor(Config):
    name: Literal["ConfigTriggeringAnchor"] = "ConfigTriggeringAnchor"
    value: Union[
        OptionAnchorCenter,
        OptionAnchorBottomCenter,
        OptionAnchorTopCenter,
        OptionAnchorCenterLeft,
        OptionAnchorCenterRight
    ]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"
    class Config:
        title = "Triggering Anchor"


class ConfigReferencePath(Config):
    name: Literal["ConfigReferencePath"] = "ConfigReferencePath"
    value: str = "[[100, 200], [200, 300], [300, 400]]"
    type: Literal["string"] = "string"
    field: Literal["textInput"] = "textInput"
    class Config:
        title = "Referans Rota Koordinatları"


class ConfigDeviationThreshold(Config):
    name: Literal["ConfigDeviationThreshold"] = "ConfigDeviationThreshold"
    value: float = Field(default=50.0, ge=0.0)
    type: Literal["number"] = "number"
    field: Literal["textInput"] = "textInput"
    class Config:
        title = "Maksimum Fréchet Sapma Eşiği"


class ConfigDrawBBox(Config):
    name: Literal["ConfigDrawBBox"] = "ConfigDrawBBox"
    value: Union[ConfigDrawTrue, ConfigDrawFalse]
    type: Literal["object"] = "object"
    field: Literal["dropdownlist"] = "dropdownlist"
    class Config:
        title = "Rota ve BBox Görsellemesi"


class Detects(Output):
    value: Any
    imgUID: str = ""


class OutputPathDeviation(Output):
    name: Literal["outputPathDeviation"] = "outputPathDeviation"
    value: List[Detects]
    type: str = "list"
    class Config:
        title = "Path Deviation"


class OutputAnnotatedImage(Output):
    name: Literal["outputAnnotatedImage"] = "outputAnnotatedImage"
    value: Union[List[Image], Image, Any]
    type: str = "object"

    @validator("type", pre=True, always=True)
    def set_type_based_on_value(cls, value, values):
        val = values.get("value", value)
        if isinstance(val, list):
            return "list"
        return "object"

    class Config:
        title = "Annotated Image"


class PathDeviationConfigs(Configs):
    triggeringAnchor: ConfigTriggeringAnchor
    referencePath: ConfigReferencePath
    deviationThreshold: ConfigDeviationThreshold
    drawBBox: ConfigDrawBBox


class PathDeviationInputs(Inputs):
    inputImage: InputImage
    inputDetections: InputDetections


class PathDeviationOutputs(Outputs):
    outputPathDeviation: OutputPathDeviation
    outputAnnotatedImage: OutputAnnotatedImage


class PathDeviationRequest(Request):
    inputs: Optional[PathDeviationInputs]
    configs: PathDeviationConfigs
    class Config:
        json_schema_extra = {
            "target": "configs"
        }


class PathDeviationResponse(Response):
    outputs: PathDeviationOutputs


class PathDeviationExecutor(Config):
    name: Literal["PathDeviationExecutor"] = "PathDeviationExecutor"
    value: Union[PathDeviationRequest, PathDeviationResponse]
    type: Literal["object"] = "object"
    field: Literal["option"] = "option"
    class Config:
        title = "Path Deviation V2 Analytics"
        json_schema_extra = {
            "target": {
                "value": 0
            }
        }


class ConfigExecutor(Config):
    name: Literal["ConfigExecutor"] = "ConfigExecutor"
    value: Union[PathDeviationExecutor]
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
    type: Literal["component"] = "component"
    name: Literal["PathDeviationTracker"] = "PathDeviationTracker"
