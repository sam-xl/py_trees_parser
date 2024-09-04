import os
from glob import glob

from setuptools import find_packages, setup

package_name = "behavior_tree"

setup(
    name=package_name,
    version="0.3.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [os.path.join("resource", package_name)]),
        (os.path.join("share/", package_name), ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob(os.path.join("launch", "*launch.[pxy][yma]*")),
        ),
        (os.path.join("share", package_name, "config"), glob(os.path.join("config", "*.yml"))),
        (os.path.join("share", package_name, "trees"), glob(os.path.join("trees", "*.xml"))),
        (
            os.path.join("share", package_name, "test", "data"),
            glob(os.path.join("test", "data", "*.xml")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Erich L Foster",
    maintainer_email="e.l.f.foster@tudelft.nl",
    description="Behavior tree implementation for SAM XL",
    license="Proprietary",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "behavior_tree = behavior_tree.behavior_tree:main",
        ],
    },
)
