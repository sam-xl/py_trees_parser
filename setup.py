import os
from glob import glob

from setuptools import find_packages, setup

package_name = "py_trees_parser"

setup(
    name=package_name,
    version="0.6.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [os.path.join("resource", package_name)]),
        (os.path.join("share/", package_name), ["package.xml"]),
        (
            os.path.join("share", package_name, "test", "data"),
            glob(os.path.join("test", "data", "*.xml")),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Erich L Foster",
    maintainer_email="e.l.f.foster@tudelft.nl",
    description="A py_trees xml parser",
    license="apache 2.0",
    tests_require=["pytest"],
    entry_points={},
)
