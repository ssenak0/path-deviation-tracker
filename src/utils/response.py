import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

try:
    from sdks.novavision.src.helper.package import PackageHelper
except ImportError:
    class PackageHelper:
        def __init__(self, packageModel=None, packageConfigs=None):
            self.packageModel = packageModel
            self.packageConfigs = packageConfigs
        def build_model(self, context):
            return {"status": "mock_response"}
try:
    from capsules.PathDeviationTracker.src.models.PackageModel import (
        PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
        PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage
    )
except ImportError:
    try:
        from capsules.Package.src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
            PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage
        )
    except ImportError:
        from src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
            PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage
        )


def build_response(context):
    raw_img = getattr(context, "output_annotated_image", getattr(context, "image", None))
    outputAnnotatedImage = OutputAnnotatedImage(value=raw_img)

    outputs = PathDeviationOutputs(
        outputAnnotatedImage=outputAnnotatedImage
    )
    response = PathDeviationResponse(outputs=outputs)
    pathExecutor = PathDeviationExecutor(value=response)
    configExecutor = ConfigExecutor(value=pathExecutor)
    packageConfigs = PackageConfigs(executor=configExecutor)
    
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    
    return packageModel