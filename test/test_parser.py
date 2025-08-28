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
from xml.etree import ElementTree

import py_trees
import py_trees_ros
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory

from py_trees_parser.parser import BTParser, handle_success_on_selected

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
            assert False, f"parse raised an exception {ex}"  # noqa

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
    assert children[5].name == "Included Subtree"
    assert children[6].name == "Always Included"

    grand_children = children[4].children
    assert grand_children[0].name == "Feature 1"
    assert grand_children[1].name == "Feature 2"
    assert grand_children[2].name == "Feature 3"

    grand_children = children[5].children
    assert grand_children[0].name == "Subtree Feature 1"
    assert grand_children[1].name == "Subtree Feature 2"
    assert grand_children[2].name == "Subtree Feature 3"


@pytest.mark.parametrize(
    "child_key, synch_key, children, synch",
    [
        (True, True, ["feature_1"], True),
        (True, True, ["Feature_2"], False),
        (True, True, ["Feature_1", "Feature_2"], True),
        (True, True, ["feature_1"], True),
        (True, True, ["Feature_2"], False),
        (False, True, ["feature_1"], True),
        (False, True, ["Feature_2"], False),
        (False, True, ["Feature_1", "Feature_2"], True),
        (False, True, ["feature_1"], True),
        (False, True, ["Feature_2"], False),
        (False, False, ["feature_1"], True),
        (False, False, ["Feature_2"], False),
        (False, False, ["Feature_1", "Feature_2"], True),
        (False, False, ["feature_1"], True),
        (False, False, ["Feature_2"], False),
        (True, False, ["feature_1"], None),
        (True, False, ["Feature_2"], None),
        (True, False, ["Feature_1", "Feature_2"], None),
        (True, False, ["feature_1"], None),
        (True, False, ["Feature_2"], None),
        (True, False, ["Feature_1", "Feature_2"], None),
    ],
)
def test_SuccessOnSelected_parsing(child_key, synch_key, children, synch):
    """Test that we can parse SuccessOnSelected parameters."""
    child_str = f"{'children=' if child_key else ''}[{', '.join(children)}]"

    # choose to include synchronise parameter or not
    if synch is not None:
        synch_str = f"{'synchronise=' if synch_key else ''}{str(synch)}"
        parallel_policy = (
            f"py_trees.common.ParallelPolicy.SuccessOnSelected({child_str}, {synch_str})"
        )
    else:
        synch = True
        parallel_policy = f"py_trees.common.ParallelPolicy.SuccessOnSelected({child_str})"

    xml_str = f"<py_trees.composites.Parallel name='TestParallel' policy='$({parallel_policy})' />"
    node = ElementTree.fromstring(xml_str)

    on_selected, synchronise = handle_success_on_selected(node.attrib)

    for selected in on_selected:
        assert selected in children

    assert synchronise is synch

    assert "policy" not in node.attrib


def test_SuccessOnSelected_special_chars_in_name(setup_parser):
    """Test SuccessOnSelected can handle special characters correctly."""
    tree_file = "test_on_selected.xml"
    root = setup_parser(tree_file)
    assert isinstance(root.policy, py_trees.common.ParallelPolicy.SuccessOnSelected)
    assert len(root.policy.children) != 0
    assert root.policy.children[0].name == "¢@mera va!ue,_check?"


def test_ParallelPolicy(setup_parser):
    """Test parallel policies are handled correctly."""
    tree_file = "test_parallel_policy.xml"
    root = setup_parser(tree_file)

    assert root.name == "ParallelPolicy Test"
    for child in root.children:
        if child.name == "SuccessOnAll":
            assert isinstance(child.policy, py_trees.common.ParallelPolicy.SuccessOnAll)
        elif child.name == "SuccessOnOne":
            assert isinstance(child.policy, py_trees.common.ParallelPolicy.SuccessOnOne)
        elif child.name == "SuccessOnSelected":
            assert isinstance(child.policy, py_trees.common.ParallelPolicy.SuccessOnSelected)
            assert len(child.policy.children) != 0
            assert child.policy.children[0].name == "Feature5"
        else:
            assert False, "Received unexpected parallel policy"  # noqa
