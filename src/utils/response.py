import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../'))

try:
    from sdks.novavision.src.helper.package import PackageHelper
except ImportError as e:
    raise ImportError(f"NovaVision import failed: {e}")

try:
    from capsules.PathDeviationTracker.src.models.PackageModel import (
        PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutorConfig,
        PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage, OutputPathDeviation
    )
except ImportError:
    try:
        from capsules.Package.src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutorConfig,
            PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage, OutputPathDeviation
        )
    except ImportError:
        from src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutorConfig,
            PathDeviationResponse, PathDeviationOutputs, OutputAnnotatedImage, OutputPathDeviation
        )


def build_response(context):
    raw_img = getattr(context, "output_annotated_image", getattr(context, "image", None))
    outputAnnotatedImage = OutputAnnotatedImage(value=raw_img)
    
    outputPathDeviation = OutputPathDeviation(
        value=getattr(context, "output_path_deviation", [])
    )

    outputs = PathDeviationOutputs(
        outputAnnotatedImage=outputAnnotatedImage,
        outputPathDeviation=outputPathDeviation
    )
    response = PathDeviationResponse(outputs=outputs)
    pathExecutor = PathDeviationExecutorConfig(value=response)
    configExecutor = ConfigExecutor(value=pathExecutor)
    packageConfigs = PackageConfigs(executor=configExecutor)

    
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    
    return packageModel