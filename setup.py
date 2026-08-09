import setuptools


setuptools.setup(
    name="path-deviation-tracker",
    version="0.0.1",
    author="DigiNova",
    author_email="info@diginova.com.tr",
    description="NovaVision Path Deviation Tracker Capsule",
    url="https://github.com/novavision-ai/path-deviation-tracker",
    license="MIT",
    install_requires=["sdk", "opencv-python-headless"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    packages=[
        "novavision.path_deviation_tracker",
        "novavision.path_deviation_tracker.executors",
        "novavision.path_deviation_tracker.models",
        "novavision.path_deviation_tracker.utils",
    ],
    package_dir={"novavision.path_deviation_tracker": "src"},
    python_requires=">=3.8",
)
