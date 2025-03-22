# Copyright 2025 SAM XL
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
        xml = os.path.join(SHARE_DIR, "test", "data", tree_file)
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
        "test1.xml",
        "test6.xml",
        "test_idioms.xml",
        "test_function_parse.xml",
        "test_subtree_main.xml",
        "test_arg_substitution_main.xml",
    ],
)
def test_tree_parser(setup_parser, tree_file):
    """Test parser for the given tree files."""
    _ = setup_parser(tree_file)


def test_subtree_and_args(setup_parser):
    """Test that subtree arguments are working as expected."""
    tree_file = "test_args.xml"
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


def test_subtree_cascaded_args(setup_parser):
    """Test that cascaded args through subtrees and nested subtrees is working as expected."""
    tree_file = "test_cascade_args.xml"
    root = setup_parser(tree_file).children[0]

    assert root.name == "Subtree Selector"

    for child in root.children:
        if isinstance(child, py_trees.behaviours.Running):
            assert child.name == "Idle"
        elif isinstance(child, py_trees.behaviours.Periodic):
            assert child.name == "Flip Eggs"
            assert child.period == 2
        else:
            assert False, f"Unexpected child node type {type(child)}"  # noqa


def test_arg_substitution_within_strings(setup_parser):
    """Test that argument substitution within strings works as expected."""
    tree_file = "test_arg_substitution_main.xml"
    root = setup_parser(tree_file)

    assert root.name == "Argument Substitution Test"

    for child in root.children:
        if isinstance(child, py_trees.behaviours.Running):
            assert child.name == "prefix_value1_suffix"
        elif isinstance(child, py_trees.behaviours.Success):
            if "multiple" in child.name:
                assert child.name == "multiple_value1_and_value2_args"
            elif "task" in child.name:
                assert child.name == "task_value2_complete"
        elif isinstance(child, py_trees.behaviours.Periodic):
            assert child.name == "periodic_value3"
            assert child.period == 3
        else:
            assert False, f"Unexpected child node type {type(child)}"  # noqa


def test_bool(setup_parser):
    """Test that True, true, False, or false are evaluated as booleans."""
    tree_file = "test_bool.xml"
    root = setup_parser(tree_file)

    assert root.name == "No Memory"
    assert root.memory is False
    assert root.children[0].name == "Memory"
    assert root.children[0].memory


def test_conditionals(setup_parser):
    """Test that conditionals include nodes as expected."""
    tree_file = "test_conditional_main.xml"
    root = setup_parser(tree_file)

    assert root.name == "Conditional Test"

    children = root.children
    assert children[0].name == "Advanced Mode Feature"
    assert children[1].name == "Non-Basic Mode Feature"
    assert children[2].name == "High Level Feature"
    assert children[3].name == "Debug Feature"
    assert children[4].name == "Conditional Selector"
    assert children[5].name == "Always Included"

    children = children[4].children
    assert children[0].name == "Feature 1"
    assert children[1].name == "Feature 2"
    assert children[2].name == "Feature 3"
