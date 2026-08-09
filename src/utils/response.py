from sdks.novavision.src.helper.package import PackageHelper

from src.models.PackageModel import (
    ConfigExecutor, OutputDetections, PackageConfigs, PackageModel,
    PathDeviationTrackerExecutorConfig, PathDeviationOutputs, PathDeviationResponse,
)


def build_response(context):
    output = OutputDetections(value=context.output_detections)
    response = PathDeviationResponse(outputs=PathDeviationOutputs(outputDetections=output))
    executor = PathDeviationTrackerExecutorConfig(value=response)
    configs = PackageConfigs(executor=ConfigExecutor(value=executor))
    return PackageHelper(packageModel=PackageModel, packageConfigs=configs).build_model(context)
