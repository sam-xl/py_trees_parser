from rclpy import logging

from ament_index_python.packages import get_package_share_directory
from behavior_tree.parser import BTParser

import os

SHARE_DIR = get_package_share_directory("behavior_tree")


def test_simple_tree():
    xml = os.path.join(SHARE_DIR, "test/data/test1.xml")
    logger = logging.get_logger("parse_test")
    logger.set_level(logging.LoggingSeverity.DEBUG)
    parser = BTParser(xml, logging.get_logger("parse_test"))
    try:
        parser.parse()
    except Exception as ex:
        assert False, f"parse raised an exception {ex}"


def test_complex_tree():
    xml = os.path.join(SHARE_DIR, "test/data/test6.xml")
    logger = logging.get_logger("parse_test")
    logger.set_level(logging.LoggingSeverity.DEBUG)
    parser = BTParser(xml, logging.get_logger("parse_test"))
    try:
        parser.parse()
    except Exception as ex:
        assert False, f"parse raised an exception {ex}"


if __name__ == "__main__":
    test_simple_tree()
    test_complex_tree()
