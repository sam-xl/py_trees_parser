from setuptools import find_packages, setup

package_name = "behavior_tree"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        ("share/" + package_name + "/test/data/", ["test/data/test1.xml", "test/data/test6.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Erich L Foster",
    maintainer_email="e.l.f.foster@tudelft.nl",
    description="Behavior tree implementation for SAM XL",
    license="BSD",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": ["inspection_tree = behavior_tree.inspection_tree:main"],
    },
)
