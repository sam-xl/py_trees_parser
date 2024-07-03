# Behavior Tree

This is the SAM XL behavior tree module. It contains behaviors that are
developed for Thermoplast project but could be reusable in other applications.

## Dependencies

- damage_inspection_msgs
- ElementTree
- geometry_msgs
- ros-humble
- ros-humble-py-trees
- ros-humble-py-trees-ros-interfaces
- ros-humble-py-trees-ros
- sensor_msgs
- std_srvs

## Behaviors

- `ImageSubscriber` ([`py_trees_ros.subscribers.ToBlackboard`]): Subscribe to
  the Image message and write an Image (sensor_msgs/Image) to the blackboard.
- `MoveRobot` ([`py_trees_ros.actions.ActionClient`]): Move robot along
  waypoints.

## XML Parser

The Behavior Tree Parser (`BTParse`) is a Python module that allows you to
parse an XML file representing a behavior tree and construct the corresponding
behavior tree using the PyTrees library. It supports composite nodes, behavior
nodes from PyTrees, and custom behavior nodes defined in your local library.

### Basic Usage

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

### Sub-Trees

It is possible to include sub-trees in the xml file containing a behavior tree. This is made possible via the following:

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="location/of/subtree.xml" parse="xml" />
</subtree>
```

The included subtree should be a complete tree, but can only contain one root.
It is possible to include multiple sub-trees and a sub-tree can also include
another subtree. However, be aware that the all directories are reltative to the main.
For example, if we have four behavior tree files in a directory like so:

```
config                                                                                                                                                                                                                                │
├── main.xml                                                                                                                                                                                                              │
└── subtree
    ├── subtree1.xml                                                                                                                                                                                                             │
    ├── subtree2.xml                                                                                                                                                                                                                │
    └── subtree3.xml
```

and the following is our main.xml

```xml
<py_trees.composites.Parallel name="Subtree Tutorial" synchronise="False">
    <subtree xmlns:xi="http://www.w3.org/2001/XInclude">
        <xi:include href="subtree/subtree1.xml" parse="xml" />
    </subtree>
    <subtree xmlns:xi="http://www.w3.org/2001/XInclude">
        <xi:include href="subtree/subtree2.xml" parse="xml" />
    </subtree>
</py_trees.composites.Parallel>
```

and we then include `subtree3.xml` in `subtree1.xml` the location of
`subtree3.xml` must still be relative to `main.xml`:

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="subtree/subtree3.xml" parse="xml" />
</subtree>
```

## Running the Behavior Tree

### Launch the Behavior Tree:

```bash
ros2 launch behavior_tree thermoplast.launch.py
```

### Render a Tree

```shell
    py-trees-render -b behavior_tree.thermoplast_tree.create_tree
```

### Launch Parameters

The following launch parameters apply to `thermoplast.launch.py`

| Parameter Name     | Description                                     | Default Value          |
| :---               | :---                                            | :---:                  |
| tree_file          | Configuration containing configuration of node  | "thermoplast.xml"      |
| rgb_image_topic    | Topic to listen to for rgb image messages       | "~/camera/image"       |
| depth_image_topic  | Topic to listen to for rgb image messages       | "~/camera/depth/image" |

## Relevant Links

<!-- links -->
[py_trees_ros.subscribers.ToBlackboard]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#py_trees_ros.subscribers.ToBlackboard
[py_trees_ros.actions.ActionClient]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#module-py_trees_ros.action_clients
[capture_image]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/SaveImage.action?ref_type=heads
[damage_inspection]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/DetectDamage.action?ref_type=heads
[py_trees.timers.Timer]: https://py-trees.readthedocs.io/en/release-2.2.x/modules.html#py_trees.timers.Timer
