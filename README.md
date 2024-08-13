# Behavior Tree

This is the SAM XL behavior tree module. It contains behaviors that are
developed for Thermoplast project but could be reusable in other applications.

## Dependencies

- abb_robot_msgs
- damage_inspection_msgs
- ElementTree
- geometry_msgs
- object_segmentation
- object_segmentation_msgs
- python-pcl
- ros-humble
- ros-humble-py-trees
- ros-humble-py-trees-ros-interfaces
- ros-humble-py-trees-ros
- ros2_numpy
- sensor_msgs
- std_srvs

## Robot Node

There is a single robot node which will live in the blackboard under the state client (see
Blackboards for more information about this). The intention of the robot node is to be the
location for image/sensor subscriptions, joint state subscriptions, and the tf buffer.
Additionally, any trigger services that may need to be run can be accessed via the
`Robot.command` function, where the command to be called is passed via a string. These
commands are defined as a dictionary within the robot node. As for the tf tree one obtains
transforms from the robot node via the `Robot.lookup_transform` function. This is just a
convenience wrapper to the `tf2_ros.lookup_transform` function and is used in the same manner.

## Blackboards

- `State`: This blackboard contains the keys related to the state of the robot, which includes
  the robot node and the state.
- `Perception`: This blackboard contains the keys related to the perception stack of the robot,
  which includes images, point clouds, objects, etc.
- `Movement`: This blackboard contains the keys related to the movement of the robot, which
  would include things like waypoints.

When creating the blackboards you would want to follow the pattern below:

```python
import py_tress

from behavior_tree import Robot
from behavior_tree.data import Blackboards

blackboard = Blackboards()
blackboard.state.register_key(key="state", access=py_trees.common.Access.WRITE)
blackboard.state.state = State()
blackboard.state.register_key(key="robot", access=py_trees.common.Access.WRITE)
blackboard.state.robot = Robot()
blackboard.perception.register_key(key="objects", access=py_trees.common.Access.WRITE)
blackboard.perception.objects = None
blackboard.movement.register_key(key="waypoints", access=py_trees.common.Access.WRITE)
blackboard.movement.waypoints = None
```

It is not necessary to register every client when creating the blackboard, rather you can
register the ones you need/want. Additionally, for variables on the blackboard like "waypoints"
or "objects" if you attempt to access them before they have been set you will receive a `KeyError`,
so be aware of this when accessing variables.

Additionally, be aware that the Robot node only needs to be created once and should be done when
creating the tree.

## Decorators

- `RepeatFromBlackboard`: This is a decorator similar to the `py_trees.decorators.Repeat`, however
  instead of having the number of successes specified when creating the `Repeat` decorator a
  `num_key` is specified. The `num_key` parameter is a key in the blackboard where the decorator
  will look for the number of times to repeat the child behaviors. The number of repitions will be
  updated each time `initialize` is called. This decorator will return `RUNNING` until the children
  have been run the number of times in the `num_key` and then will return `SUCCESS` or `FAILURE`
  depending on the success of failure state of the children.

## Behaviors

- `SaveImage` ([`py_python.behavior.Behaviour`]): Save the current image for "camera" to
  `perception` blackboard.
- `SaveImageToDrive` ([`py_python.behavior.Behaviour`]): Save the current image for "camera" to
  drive.
- `SaveDepthImage` ([`py_python.behavior.Behaviour`]): Save the current image for "camera" to
  `perception` blackboard.
- `SaveDepthImageToDrive` ([`py_python.behavior.Behaviour`]): Save the current image for "camera"
  to dive.
- `SavePointCloud` ([`py_python.behavior.Behaviour`]): Save the current point cloud for "camera" to
  `perception` blackboard.
- `ActionClient` ([`py_trees.behaviour.Behaviour`]): This is an abstract action client class that
  sets up most of the steps that are necessary for an ActionClient. This requires that any derived class
  create a `get_request` function, which creates the specific goal needed for the desired action.
- `ServiceClient` ([`py_trees.behaviour.Behaviour`]): This is an abstract service client class that sets
  up most of the steps that are necessary for a ServiceClient. This requires that any derived class
  create a `get_request` function, which creates the specific goal needed for the desired service,
  additionally it requires a `validate_service_response` function that will eventually set `self.success`
  depending if the response from the service was valid or not.

### Action Behaviors

- `DetectObjects` ([`behavior_tree.behaviors.ActionClient`]): An action client that requests
  object detections from the `ObjectDetection` action server and then saves them to the
  `perception.objects` blackboard variable.
- `DetectIDs` ([`behavior_tree.behaviors.ActionClient`]): An action client that requests
  object id detections from the `ToolIDDetector` action server and then updates the
  `perception.objects` blackboard variable. It matches the detected id to the closest object using the
  pixel location.
- `MoveCartesian` ([`behavior_tree.behaviors.ActionClient`]): Move the robot along the given waypoints.
- `MoveJoint` ([`behavior_tree.behaviors.ActionClient`]): Move robot to a joint configuration by providing a `link_name` and `target_pose_key`.
- `MoveToNamedTarget` ([`behavior_tree.behaviors.ActionClient`]): Move the robot to a joint_configuration predefined by name.

### Service Behaviors

- `SetABBIOSignal` ([`behavior_tree.behaviors.ServiceClient`]): This behavior triggers an IO signal by calling
  a specified ABB ROS 2 service (default is `/rws_client/set_io_signal`). It supports setting the IO signal
  to either high or low based on the trigger_on parameter. The behavior validates the response to
  determine if the service call was successful, and updates its status accordingly. This behavior is
  useful for controlling external devices connected to the ABB like pneumatic cylinders via ROS 2 services.

### Pick & Place pipeline
The components that could make up the process of `pick&place` are created as `ActionClient` behaviors and can be found in `/behavior_tree/behaviors/move.py`.
We distinguish three different types of motion requests:
- `MoveCartesian`: By providing among others a `list of waypoints`, motions like __approaching__ a pick/place pose or __retreating__ from one 
could be achieved with cartesian planning ensuring a linear movement.
- `MoveJoint`: To reach a specific joint pose in order to __rotate end-effector__ for example, the user can send a `MoveJoint` request by specifying a `target_pose_key` where the _goal pose_ would be stored.
- `MoveToNamedTarget`: By providing a priorly configured `named_target` i.e. a `named_joint_configuration`, the robot can move to "general areas of interest" notably __general pick/place location__, __inspection_station__ or __open/close fingers__ for a finger gripper...
_____
It is necessary to create a specific __gripper_behavior__ depending on its type (fingers, suction, magnetic...) and how it is connected to the robot system. One example to be used in Thermoplast is `SetABBIOSignal` which can activate/deactivate the signal of the magnetic gripper.
____
The _pick & place pipeline_ can then be composed of the different motion behaviors the behavior_tree provides and easily costumized to the specific use-case in place. See subtrees examples: `pick.xml` and `place.xml`, the `pick_and_place.xml` tree is created by providing the formers as substrees.

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
    py-trees-render -b behavior_tree.behavior_tree.thermoplast_tree
```

### Launch Parameters

The following launch parameters apply to `thermoplast.launch.py`

| Parameter Name               | Description                                      | Default Value                   |
| :---                         | :---                                             | :---                            |
| config_file                  | Configuration containing configuration of node   | "thermoplast.yml"               |
| webcam_image_topic           | Topic to listen to for webcam image messages     | "/webcam/camera/color/image"    |
| realsense_image_topic        | Topic to listen to for realsense image messages  | "/realsense/camera/color/image" |
| depth_image_topic            | Topic to listen to for depth image messages      | "/realsense/camera/depth/image" |
| webcam_info_topic            | Topic to listen to for webcam camera inf   o     | "/webcam/camera/color/image"    |
| realsense_rbg_info_topic     | Topic to listen to for realsense rbg camera info | "/realsense/camera/color/image" |
| depth_info_topic             | Topic to listen to for depth camera info         | "/realsense/camera/depth/image" |
| pointcloud_topic             | Topic to listen to for point cloud messages      | "/realsense/camera/depth/image" |
| joint_state_topic            | Topic to listen to for joint state messages      | "~/joint_states"                |
| compute_cartesian_path_topic | Topic to publish cartesian path messages too     | "~/compute_cartesian_path"      |

## Relevant Links

<!-- links -->
[py_trees_ros.subscribers.ToBlackboard]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#py_trees_ros.subscribers.ToBlackboard
[py_trees_ros.actions.ActionClient]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#module-py_trees_ros.action_clients
[behavior_tree.behaviors.ServiceClient]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/behavior_tree/-/blob/humble/behavior_tree/behaviors/service_client.py
[capture_image]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/SaveImage.action?ref_type=heads
[damage_inspection]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/DetectDamage.action?ref_type=heads
[py_trees.timers.Timer]: https://py-trees.readthedocs.io/en/release-2.2.x/modules.html#py_trees.timers.Timer
