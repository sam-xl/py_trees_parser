import os

import py_trees_ros
import pytest
from ament_index_python.packages import get_package_share_directory
from conftest import log_test_execution
from rclpy import logging

from behavior_tree.parser import BTParser

SHARE_DIR = get_package_share_directory("behavior_tree")


@pytest.mark.parametrize(
    "tree_file, logger_name",
    [
        ("test/data/test1.xml", "parse_test"),
        ("test/data/test6.xml", "parse_test"),
        ("test/data/test_subtree_main.xml", "subtree_test"),
    ],
)
@log_test_execution
def test_simple_tree(ros_init, tree_file, logger_name):
    xml = os.path.join(SHARE_DIR, tree_file)
    logger = logging.get_logger(logger_name)
    logger.set_level(logging.LoggingSeverity.DEBUG)
    parser = BTParser(xml, logging.get_logger("parse_test"))
    try:
        root = parser.parse()
        py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
    except Exception as ex:
        assert False, f"parse raised an exception {ex}"
