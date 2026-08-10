from sdks.novavision.src.helper.package import PackageHelper

from novavision.path_deviation_tracker.models.PackageModel import (
    ConfigExecutor, OutputDetections, PackageConfigs, PackageModel,
    PathDeviationTrackerExecutor, PathDeviationOutputs, PathDeviationTrackerExecutorResponse,
)


def build_response(context):
    output = OutputDetections(value=context.output_detections)
    response = PathDeviationTrackerExecutorResponse(outputs=PathDeviationOutputs(outputDetections=output))
    executor = PathDeviationTrackerExecutor(value=response)
    configs = PackageConfigs(executor=ConfigExecutor(value=executor))
    return PackageHelper(packageModel=PackageModel, packageConfigs=configs).build_model(context)
