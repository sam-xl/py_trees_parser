# Behavior Tree
This is the SAM XL behavior tree module.

## XML Parser
The Behavior Tree Parser is a Python module that allows you to parse an XML file
representing a behavior tree and construct the corresponding behavior tree using
the PyTrees library. It supports composite nodes, behavior nodes from PyTrees,
and custom behavior nodes defined in your local library.

### Usage
To use the Behavior Tree Parser, follow these steps:

Create an XML file that represents your behavior tree. The XML structure should
define the nodes and their attributes. It should be similar to the following
```xml
    <py_trees.composites.Parallel name="TutorialOne" synchronise="False">
        <py_trees.composites.Sequence name="Topics2BB" memory="False">
            <py_trees_ros.battery.ToBlackboard name="Battery2BB" topic_name="/battery/state" qos_profile="py_trees_ros.utilities.qos_profile_unlatched()" threshold="30.0" />
        </py_trees.composites.Sequence>
        <py_trees.composites.Selector name="Tasks" memory="False">
            <py_trees.behaviours.Running name="Idle" />
            <py_trees.behaviours.Periodic name="Flip Eggs" n="2" />
        </py_trees.composites.Selector>
    </py_trees.composites.Parallel>
```

Assuming the above is saved in `behavior_tree.xml` it can be imported via the following code:
```python
from behavior_tree import parser
import py_trees
from rclpy import logging

logger = logging.get_logger('parser')
logger.set_level(logging.LoggingSeverity.DEBUG)

# Parse the XML file and create the behavior tree:
xml_file = "behavior_tree.xml"
parser = BTParse(xml_file, logger)
behavior_tree = parser.parse()
```

Use the behavior tree as needed in your application.

## Dependencies
ros-humble
ros-humble-py-trees
ros-humble-py-trees-ros-interfaces
ros-humble-py-trees-ros
ros-humble-py-trees-ros-tutorials
