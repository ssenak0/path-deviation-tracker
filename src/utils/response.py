from sdks.novavision.src.helper.package import PackageHelper
try:
    from components.PathDeviationTracker.src.models.PackageModel import (
        PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
        PathDeviationResponse, PathDeviationOutputs, OutputPathDeviation,
        OutputAnnotatedImage, Detects
    )
except ImportError:
    try:
        from components.Package.src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
            PathDeviationResponse, PathDeviationOutputs, OutputPathDeviation,
            OutputAnnotatedImage, Detects
        )
    except ImportError:
        from src.models.PackageModel import (
            PackageModel, PackageConfigs, ConfigExecutor, PathDeviationExecutor,
            PathDeviationResponse, PathDeviationOutputs, OutputPathDeviation,
            OutputAnnotatedImage, Detects
        )


def build_response(context):
    img_uid = getattr(context, "uID", getattr(context.request, "uID", ""))
    raw_img = getattr(context, "output_annotated_image", getattr(context, "image", None))

    raw_detections = getattr(context, "output_path_deviation", [])
    outputPathDeviation = OutputPathDeviation(value=raw_detections)
    outputAnnotatedImage = OutputAnnotatedImage(value=raw_img)

    outputs = PathDeviationOutputs(
        outputPathDeviation=outputPathDeviation,
        outputAnnotatedImage=outputAnnotatedImage
    )
    response = PathDeviationResponse(outputs=outputs)
    pathExecutor = PathDeviationExecutor(value=response)
    configExecutor = ConfigExecutor(value=pathExecutor)
    packageConfigs = PackageConfigs(executor=configExecutor)
    
    package = PackageHelper(packageModel=PackageModel, packageConfigs=packageConfigs)
    packageModel = package.build_model(context)
    
    return packageModel