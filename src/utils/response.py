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
    package = PackageHelper(packageModel=PackageModel, packageConfigs=configs)
    packageModel = package.build_model(context)
    return packageModel
