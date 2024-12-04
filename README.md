# Behavior Tree

This is the SAM XL behavior tree module. It contains generic behaviors for perception and for simple motion planning and executing.

## Dependencies

- ElementTree
- geometry_msgs
- python-pcl
- ros-humble
- ros-humble-py-trees
- ros-humble-py-trees-ros-interfaces
- ros-humble-py-trees-ros
- ros2_numpy
- sensor_msgs
- std_srvs

## Robot Node

There is a single robot node which will live in the blackboard under the state
client (see Blackboards for more information about this). The intention of the
robot node is to be the location for image/sensor subscriptions, joint state
subscriptions, and the tf buffer. Additionally, any trigger services that may
need to be run can be accessed via the `Robot.command` function, where the
command to be called is passed via a string. These commands are defined as a
dictionary within the robot node. As for the tf tree one obtains transforms
from the robot node via the `Robot.lookup_transform` function. This is just a
convenience wrapper to the `tf2_ros.lookup_transform` function and is used in
the same manner.

For the `Robot` node to be completely setup it is required to run `robot.setup()`.
This will load the `triggers`, and `sensors` and will setup the subscriptions for
those items.

### Sensor Configuration

To configure the sensors to be used by the robot node, yaml can be passed to
the sensors parameter. The yaml should contain all sensors types, the sensor
name, and the topic to listen to. Additionally, any `camera_info` with their
sensor name and topics should also be included.

#### Example

```yaml
sensors:
  rgb:
    webcam: "/camera/webcam/color/image_raw"
    realsense: "/camera/realsense/color/image_raw"
  depth:
    realsense: "/camera/realsense/depth/image_rect_raw"
  camera_info:
    webcam_rgb: "/camera/webcam/color/camera_info"
    realsense_rgb: "/camera/realsense/color/camera_info"
    realsense_depth: "/camera/realsense/depth/camera_info"
```

### Trigger Configuration<a name="trigger-configuration"/>

Similarly to the sensor configuration the robot node can have triggers configured
via passing a yaml the `triggers` parameter. The triggers should contain the name
of the service and the service topic that the trigger service is listening on.

#### Example

```yaml
triggers:
    service1: /triggers/service1
    service2: /triggers/service2
    service3: /triggers/service3
```

## Blackboards

- `State`: This blackboard contains the keys related to the state of the robot,
  which includes the robot node and the state.
- `Perception`: This blackboard contains the keys related to the perception
  stack of the robot, which includes images, point clouds, objects, etc.
- `Movement`: This blackboard contains the keys related to the movement of the
  robot, which would include things like waypoints.

When creating the blackboards you would want to follow the pattern below:

```python
import py_tress

from behavior_tree import Robot
from behavior_tree.data import Blackboards

blackboard = Blackboards()
blackboard.set("state", key="state", value=State())
robot = Robot()
robot.setup()  # required for sensor and trigger setup
blackboard.set("state", key="robot", value=robot)
blackboard.set("perception", key="objects", value=None)
blackboard.set("movement", key="waypoints", value=None)
```

It is not necessary to register every client when creating the blackboard,
rather you can register the ones you need/want. Additionally, for variables on
the blackboard like "waypoints" or "objects" if you attempt to access them
before they have been set you will receive a `KeyError`, so be aware of this
when accessing variables.

Additionally, be aware that the `Robot` node only needs to be created once and
should be done when creating the tree. Ideally, one would create the tree and
then add the `Robot` node to the tree in the following way:

```
    tree = py_trees_ros.trees.BehaviourTree(root=root, unicode_tree_debug=True)
    tree.setup(node=robot, timeout=15.0)
```

This will set the `Robot` node as the `py_trees_ros` node. Thus only one ros
node will exist in the tree unless another is created.

## Decorators

- `ContinueCancel` ([`py_trees.decorators.Decorator`]): This decorator waits
  for a key press from the user, it will continue to return
  `py_trees.common.Status.RUNNING` until the `continue_key` or `cancel_key` is
  pressed, at which point it will return `py_trees.common.Status.SUCCESS` or the
  childs last status, respectively.
- `RepeatFromBlackboard`: This is a decorator similar to the
  `py_trees.decorators.Repeat`, however instead of having the number of
  successes specified when creating the `Repeat` decorator a `num_key` is
  specified. The `num_key` parameter is a key in the blackboard where the
  decorator will look for the number of times to repeat the child behaviors.
  The number of repitions will be updated each time `initialize` is called.
  This decorator will return `RUNNING` until the children have been run the
  number of times in the `num_key` and then will return `SUCCESS` or `FAILURE`
  depending on the success of failure state of the children.

## Behaviors

- `ContinueCancel` ([`py_trees.behaviour.Behaviour`]): This behavior waits
  for a key press from the user, it will continue to return
  `py_trees.common.Status.RUNNING` until the `continue_key` or
  `cancel_key` is pressed, at which point it will return
  `py_trees.common.Status.SUCCESS` or `py_trees.common.Status.FAILURE`,
  respectively.
- `EmitFromFile` (`py_trees.behaviour.Behaviour`): A behavior that sets a
  blackboard variable given data from a file. Each time the behavior is ticked
  it will read another line from a file and set a blackboard variable. If all
  messages have been published it will continue from the beginning of the file.
- `SaveImage` ([`py_python.behavior.Behaviour`]): Save the current image for
  "camera" to `perception` blackboard.
- `SaveImageToDrive` ([`py_python.behavior.Behaviour`]): Save the current image
  for "camera" to drive.
- `SavePointCloud` ([`py_python.behavior.Behaviour`]): Save the current point
  cloud for "camera" to `perception` blackboard.
- `Trigger` ([`py_trees.behaviour.Behaviour`]`]): Send a trigger for the given
  trigger name. (see [triggers](#trigger-configuration) for details)
- `TransformToBlackboard` ([`py_python.behavior.Behaviour`]): Save the requested
  transformation to the blackboard.

### Action Behaviors

- `ActionClient` ([`py_trees.behaviour.Behaviour`]): This is an abstract action
  client class that sets up most of the steps that are necessary for an
  ActionClient. This requires that any derived class create `get_goal`
  `validate_result` functions, which creates the specific goal needed for
  the desired action and validates/processes the action result, respectively.
  The `get_goal` method should return the goal request for the action while
  `validate_result` should return a `tuple[bool, str]` contains the result and
  the feedback string.
- `Move` ([`behavior_tree.behaviors.ActionClient`]): Execute robot motion
  along the given waypoints.
- `PlanJointMotion` ([`behavior_tree.PlanJoinSpaceMotion`]): Plan
  robot movement to a joint configuration by providing a `link_name` and
  `target_pose_key`.
- `PlanToNamedTarget` ([`behavior_tree.PlanJoinSpaceMotion`]): Plan
  robot movement to a joint_configuration predefined by name.

### Service Behaviors

- `ServiceClient` ([`py_trees.behaviour.Behaviour`]): This is an abstract
  service client class that sets up most of the steps that are necessary for a
  ServiceClient. This requires that any derived class create a `get_request`
  function, which creates the specific goal needed for the desired service,
  additionally it requires a `validate_service_response` function that will
  eventually set `self.success` depending if the response from the service was
  valid or not.
- `PlanCartesian` ([`behavior_tree.ServiceClient`]): Plan robot
  movement along the given waypoints.

### Pick & Place pipeline

The components that could make up the process of `pick&place` are created as
`ActionClient`s and `ServiceClient`s. The planning and motion are separate
and so a robot motion consists of a planning stage followed by an execution
stage. The motion is accomplished via the action `behavior_tree.actions.Move`.

We distinguish three different types of motion requests:

- `behavior_tree.services.PlanCartesian`: By providing among others a
  `list of waypoints`, motions like __approaching__ a pick/place pose or
  __retreating__ from one could be achieved with cartesian planning ensuring a
  linear motion.
- `behavior_tree.actions.PlanJointMotion`: To reach a specific joint pose in
  order to __rotate end-effector__ for example, the user can send a `Joint`
  request by specifying a `target_pose_key` where the _goal pose_ would be
  stored.
- `behavior_tree.actions.PlanToNamedTarget`: By providing a priorly configured
  `named_target` i.e. a `named_joint_configuration`, the robot can move to
  "general areas of interest" notably __general pick/place location__,
  __inspection_station__ or __open/close fingers__ for a finger gripper...

_____
It is necessary to create a specific __gripper_behavior__ depending on its type
(fingers, suction, magnetic...) and how it is connected to the robot system.
One example used in Thermoplast is `SetABBIOSignal` which can
activate/deactivate the signal of the magnetic gripper.
____
The _pick & place pipeline_ can then be composed of the different motion
behaviors the behavior_tree provides and easily costumized to the specific
use-case in place. See subtrees examples: `pick.xml` and `place.xml`, the
`pick_and_place.xml` tree is created by providing the formers as substrees.

## XML Parser

The Behavior Tree Parser (`BTParse`) is a Python module that allows you to
parse an XML file representing a behavior tree and construct the corresponding
behavior tree using the PyTrees library. It supports composite nodes, behavior
nodes from PyTrees, and custom behavior nodes defined in your local library.

For any parameter that are code the code must be surrounded by `$()`. This
allows the parser know that the following parameter value is in fact code
and should be evaluated as code.

Idioms are also now supported. An idiom is a special function that produces
a behavior tree, the function is expected to either take no children, takes
a list of children via parameters "taks" or "subtrees", or takes a single
child via parameter "behavior". The xml parser will treat children in the
same way that it treats children for all other behaviors. That is the
children should be a subnode of the idiom node.

### Basic Usage

To use the Behavior Tree Parser, follow these steps:

Create an XML file that represents your behavior tree. The XML structure should
define the nodes and their attributes. It should be similar to the following:

```xml
<py_trees.composites.Parallel name="TutorialOne" synchronise="False">
    <py_trees.composites.Sequence name="Topics2BB" memory="False">
        <py_trees_ros.battery.ToBlackboard name="Battery2BB"
            topic_name="/battery/state"
            qos_profile="$(py_trees_ros.utilities.qos_profile_unlatched())"
            threshold="30.0" />
    </py_trees.composites.Sequence>
    <py_trees.composites.Selector name="Tasks" memory="False">
        <py_trees.behaviours.Running name="Idle" />
        <py_trees.behaviours.Periodic name="Flip Eggs" n="2" />
    </py_trees.composites.Selector>
</py_trees.composites.Parallel>
```

Assuming the above is saved in `behavior_tree.xml` it can be imported via the
following code:

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

It is possible to include sub-trees in the xml file containing a behavior tree.
This is made possible via the following:

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="location/of/subtree.xml" parse="xml" />
</subtree>
```

The included subtree should be a complete tree, but can only contain one root.
It is possible to include multiple sub-trees and a sub-tree can also include
another subtree. However, be aware that the all directories are reltative to
the main. For example, if we have four behavior tree files in a directory like
so:

```
config
├── main.xml
└── subtree
    ├── subtree1.xml
    ├── subtree2.xml
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

It is also possible to use arguments for subtrees. The syntax of which looks like

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <arg name="foo" value="bar" />
    <xi:include href="subtree/subtree.xml" parse="xml" />
</subtree>
```

with subtree

```xml
<py_trees.composites.Sequence name="Arg Tutorial">
    <py_trees.behaviors.Success name="${foo}" />
</py_trees.composites.Sequence>
```

## Running the Behavior Tree

### Launch the Behavior Tree:

```bash
ros2 launch behavior_tree example_tree.launch.py
```

### Render a Tree

To be able to render tree, open a terminal and run the following:

```shell
    py-trees-render behavior_tree.behavior_tree.view_tree -b -v --kwargs='{"xml_file": "name_tree.xml"}'
```

**Make sure the value of `share_path` ros parameter is set to your own package as this method looks for the xml file under `share_path/trees/`.**

### Viewing the Behavior Tree

There are two ways to view the Behavior Tree. The first is has a GUI and
takes advantage of py-trees-ros-viewer. To view the behavior tree using
this method you simply run the following command:

```shell
py-trees-tree-viewer
```

A GUI will appear that allows you to view the behavior tree. For more
details see the
[documentation](https://github.com/splintered-reality/py_trees_ros_viewer).

The second method for viewing the behavior tree will result in the behavior
tree getting printed in the terminal. The tree will be updated on tick. This
can be achieved with the following command:

```shell
py-trees-tree-watcher -b
```

This command will print the current state of the behavior tree including the
blackboard. To see more details run `py-trees-tree-watcher --help`.

### Launch Parameters

The following launch parameters apply to `thermoplast.launch.py`

| Parameter Name               | Description                                      | Default Value                         |
| :---                         | :---                                             | :---                                  |
| config_file                  | Configuration containing configuration of node   | "thermoplast.yml"                     |
| webcam_image_topic           | Topic to listen to for webcam image messages     | "/camera/webcam/color/image"          |
| webcam_info_topic            | Topic to listen to for webcam camera info        | "/camera/webcam/color/camera_info"    |
| realsense_image_topic        | Topic to listen to for realsense image messages  | "/camera/realsense/color/image"       |
| realsense_rgb_info_topic     | Topic to listen to for realsense rgb camera info | "/camera/realsense/color/camera_info" |
| depth_image_topic            | Topic to listen to for depth image messages      | "/camera/realsense/depth/image"       |
| depth_info_topic             | Topic to listen to for depth camera info         | "/camera/realsense/depth/camera_info" |
| pointcloud_topic             | Topic to listen to for point cloud messages      | "/camera/realsense/depth/image"       |
| joint_state_topic            | Topic to listen to for joint state messages      | "~/joint_states"                      |
| compute_cartesian_path_topic | Topic to publish cartesian path messages too     | "~/compute_cartesian_path"            |

## Relevant Links

<!-- links -->
[py_trees_ros.subscribers.ToBlackboard]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#py_trees_ros.subscribers.ToBlackboard
[py_trees_ros.actions.ActionClient]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#module-py_trees_ros.action_clients
[behavior_tree.behaviors.ServiceClient]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/behavior_tree/-/blob/humble/behavior_tree/behaviors/service_client.py
[py_trees.timers.Timer]: https://py-trees.readthedocs.io/en/release-2.2.x/modules.html#py_trees.timers.Timer
