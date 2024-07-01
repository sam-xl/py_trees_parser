import os
import unittest

import py_trees_ros
import rclpy
from ament_index_python.packages import get_package_share_directory
from rclpy import logging

from behavior_tree.parser import BTParser

SHARE_DIR = get_package_share_directory("behavior_tree")


class TestParser(unittest.TestCase):
    def setUp(self):
        rclpy.init()

    def tearDown(self):
        rclpy.try_shutdown()

    def test_simple_tree(self):
        xml = os.path.join(SHARE_DIR, "test/data/test1.xml")
        logger = logging.get_logger("parse_test")
        logger.set_level(logging.LoggingSeverity.DEBUG)
        parser = BTParser(xml, logging.get_logger("parse_test"))
        try:
            root = parser.parse()
            py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
        except Exception as ex:
            assert False, f"parse raised an exception {ex}"

    def test_subtree(self):
        xml = os.path.join(SHARE_DIR, "test/data/test_subtree_main.xml")
        logger = logging.get_logger("subtree test")
        logger.set_level(logging.LoggingSeverity.DEBUG)
        parser = BTParser(xml, logging.get_logger("subtree test"))
        try:
            root = parser.parse()
            py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
        except Exception as ex:
            assert False, f"parse raised an exception {ex}"

    def test_complex_tree(self):
        xml = os.path.join(SHARE_DIR, "test/data/test6.xml")
        logger = logging.get_logger("parse_test")
        logger.set_level(logging.LoggingSeverity.DEBUG)
        parser = BTParser(xml, logging.get_logger("parse_test"))
        try:
            root = parser.parse()
            py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
        except Exception as ex:
            assert False, f"parse raised an exception {ex}"


if __name__ == "__main__":
    unittest.main()
