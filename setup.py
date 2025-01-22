# Copyright 2025 SAM-XL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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
