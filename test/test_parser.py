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
    rclpy.init()
    yield
    rclpy.shutdown()


@pytest.fixture
def setup_parser(ros_init):
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
    _ = setup_parser(tree_file)


def test_subtree_and_args(setup_parser):
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
            assert False, f"Unexpected child node type {type(child)}"
