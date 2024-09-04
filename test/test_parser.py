import os

import py_trees_ros
import pytest
import rclpy
from ament_index_python.packages import get_package_share_directory
from conftest import log_test_execution

from behavior_tree.parser import BTParser

SHARE_DIR = get_package_share_directory("behavior_tree")

rclpy.logging.get_logger("BTParser").set_level(rclpy.logging.LoggingSeverity.DEBUG)


@pytest.mark.parametrize(
    "tree_file",
    [
        "test/data/test1.xml",
        "test/data/test6.xml",
        "test/data/test_subtree_main.xml",
        "test/data/test_idioms.xml",
    ],
)
@log_test_execution
def test_simple_tree(ros_init, tree_file):
    xml = os.path.join(SHARE_DIR, tree_file)
    parser = BTParser(xml)
    try:
        root = parser.parse()
        py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
    except Exception as ex:
        assert False, f"parse raised an exception {ex}"
