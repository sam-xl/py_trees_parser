from behavior_tree.parser import (
    BTParser
)
from xml.etree import ElementTree as ET
from rclpy import logging

def test_simple_tree():
    # the following example comes from https://py-trees-ros-tutorials.readthedocs.io/en/release-2.1.x/tutorials.html#before-we-start
    simple_tree = """
    <py_trees.composites.Parallel name="TutorialOne" policy="py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=False)">
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

def test_complex_tree():
    # the following example comes from https://py-trees-ros-tutorials.readthedocs.io/en/release-2.1.x/tutorials.html#before-we-start
    complex_tree = """
    <py_trees.composites.Parallel name="TutorialSix" policy="py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=False)">
        <py_trees.composites.Sequence name="Topics2BB" memory="False">
            <py_trees_ros.subscribers.EventToBlackboard name="Scan2BB" topic_name="/dashboard/scan" qos_profile="py_trees_ros.utilities.qos_profile_unlatched()" variable_name="event_scan_button" />
            <py_trees_ros.battery.ToBlackboard name="Battery2BB" topic_name="/battery/state" qos_profile="py_trees_ros.utilities.qos_profile_unlatched()" threshold="30.0" />
        </py_trees.composites.Sequence>
        <py_trees.composites.Selector name="Tasks" memory="False">
            <py_trees.decorators.EternalGuard name="Battery Low?" condition="behavior_tree.utils.check_battery_low_on_blackboard" blackboard_keys="{'battery_low_warning'}">
                <behavior_tree.behaviours.FlashLedStrip name="Flash Red" colour="red" />
            </py_trees.decorators.EternalGuard>
            <py_trees.composites.Sequence name="Scan" memory="False">
                <py_trees.behaviours.CheckBlackboardVariableValue name="Scan?" check="py_trees.common.ComparisonExpression(variable='event_scan_button', value=True, operator=operator.eq)" />
                <py_trees.composites.Selector name="Preempt?" memory="False">
                    <py_trees.decorators.SuccessIsRunning name="SuccessIsRunning">
                        <py_trees.behaviours.CheckBlackboardVariableValue name="Scan?" check="py_trees.common.ComparisonExpression(variable='event_scan_button', value=True, operator=operator.eq)" />
                    </py_trees.decorators.SuccessIsRunning>
                    <py_trees.composites.Parallel name="Scanning" policy="py_trees.common.ParallelPolicy.SuccessOnOne()">
                        <behavior_tree.behaviours.ScanContext name="Context Switch" />
                        <py_trees_ros.actions.ActionClient name="Rotate" action_type="py_trees_actions.Rotate" action_name="rotate" action_goal="py_trees_actions.Rotate.Goal()" generate_feedback_message="lambda msg: '{:.2f}%%'.format(msg.feedback.percentage_completed)" />
                        <behavior_tree.behaviours.FlashLedStrip name="Flash Blue" colour="blue" />
                    </py_trees.composites.Parallel>
                </py_trees.composites.Selector>
                <py_trees.composites.Parallel name="Celebrate" policy="py_trees.common.ParallelPolicy.SuccessOnOne()">
                    <behavior_tree.behaviours.FlashLedStrip name="Flash Green" colour="green" />
                    <py_trees.timers.Timer name="Pause" duration="3.0" />
                </py_trees.composites.Parallel>
            </py_trees.composites.Sequence>
            <py_trees.behaviours.Running name="Idle" />
        </py_trees.composites.Selector>
    </py_trees.composites.Parallel>
    """

    logger = logging.get_logger("parse_test")
    logger.set_level(logging.LoggingSeverity.DEBUG)
    parser = BTParser(complex_tree, logging.get_logger("parse_test"))
    tree = parser.parse()

if __name__ == "__main__":
    test_simple_tree()
    test_complex_tree()
