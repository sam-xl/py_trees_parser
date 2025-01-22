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
"""
Tests for the BTParser module.

These tests cover parsing behavior tree XML files, validating the
structure and contents, and ensuring the resulting py_trees.behaviour.Behaviour
instances are valid.
"""

import os

import py_trees
import py_trees_ros
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory

from py_trees_parser.parser import BTParser

SHARE_DIR = get_package_share_directory("py_trees_parser")

rclpy.logging.get_logger("BTParser").set_level(rclpy.logging.LoggingSeverity.DEBUG)


@pytest.fixture(scope="module")
def ros_init():
    """Initialize ros."""
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def setup_parser(ros_init):
    """Setup the parser and test file processing."""

    def _setup(tree_file):
        xml = os.path.join(SHARE_DIR, tree_file)
        parser = BTParser(xml, log_level=rclpy.logging.LoggingSeverity.DEBUG)
        try:
            root = parser.parse()
            py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
        except Exception as ex:
            assert False, f"parse raised an exception {ex}"

        return root

    return _setup


@pytest.mark.parametrize(
    "tree_file",
    [
        "test/data/test1.xml",
        "test/data/test6.xml",
        "test/data/test_idioms.xml",
        "test/data/test_function_parse.xml",
        "test/data/test_subtree_main.xml",
    ],
)
def test_tree_parser(setup_parser, tree_file):
    """Test parser for the given tree files."""
    _ = setup_parser(tree_file)


def test_subtree_and_args(setup_parser):
    """Test that subtree arguments are working as expected."""
    tree_file = "test/data/test_args.xml"
    root = setup_parser(tree_file)

    assert root.name == "Subtree Selector"
    for child in root.children:
        if isinstance(child, py_trees.behaviours.Running):
            assert child.name == "Idle"
        elif isinstance(child, py_trees.behaviours.Periodic):
            assert child.name == "Flip Eggs"
            assert child.period == 2
        else:
            assert False, f"Unexpected child node type {type(child)}"  # noqa
