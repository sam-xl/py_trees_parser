from behavior_tree.parser import (
    BTParseError,
    BTParser
)
from xml.etree import ElementTree as ET
from rclpy import logging

def test_simple_tree():
    # the following example comes from https://py-trees-ros-tutorials.readthedocs.io/en/release-2.1.x/tutorials.html#before-we-start
    simple_tree = """
    <py_trees.composites.Parallel name="TutorialOne" synchronise="False">
        <py_trees.composites.Sequence name="Topics2BB" memory="False">
            <py_trees_ros.battery.ToBlackboard name="Battery2BB" topic_name="/battery/state" qos_profile="py_trees_ros.utilities.qos_profile_unlatched()" threshold="30.0" />
        </py_trees.composites.Sequence>
        <py_trees.composites.Selector name="Tasks" memory="False">
            <py_trees.behaviours.Running name="Idle" />
            <py_trees.behaviours.Periodic name="Flip Eggs" n="2" />
        </py_trees.composites.Selector>
    </py_trees.composites.Parallel>
    """
    logger = logging.get_logger("parse_test")
    logger.set_level(logging.LoggingSeverity.DEBUG)
    parser = BTParser(simple_tree, logging.get_logger("parse_test"))
    tree = parser.parse()

if __name__ == "__main__":
    test_simple_tree()
