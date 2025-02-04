# py_trees Parser

This is a xml parser for processing and building a
[py_trees](https://github.com/splintered-reality/py_trees) behavior tree. The
hope is that most if not all capabilities of py_trees and
[py_trees_ros](https://github.com/splintered-reality/py_trees_ros) will be
available for xml parsing. As such, a py_trees behavior tree can be created by
simply creating an xml file.

## Dependencies

- ElementTree
- ros-humble
- ros-humble-py-trees
- ros-humble-py-trees-ros

To install dependencies you can run the following commands:

```shell
vcs import src < src/py_trees_parser/dependencies.repos
rosdep update
rosdep -q install --from-paths src/ --ignore-src -y --rosdistro "${ROS_DISTRO}"
```

where `ROS_DISTRO` is an environment variable containing the ros2 distribution
name.

## XML Parser

The Behavior Tree Parser (`BTParser`) is a Python class that allows you to
parse an XML file representing a behavior tree and construct the corresponding
behavior tree using the `py_trees` library. It supports composite nodes, behavior
nodes from `py_trees`, and custom behavior nodes defined in your local library.

### Examples

For examples see `test/data/`.

### Python Interpreter

For any parameter that is python code, the code must be surrounded by `$()`.
This allows the parser know that the following parameter value is in fact code
and should be evaluated as code. For a concrete example see below:

```xml
<py_trees_ros.battery.ToBlackboard name="Battery2BB"
    topic_name="/battery/state"
    qos_profile="$(py_trees_ros.utilities.qos_profile_unlatched())"
    threshold="30.0" />
```

In the above example the `qos_profile` is evaluated as python code. Notice to
use any python module you must use the fully qualified name.

### Idioms

Idioms are also now supported. An idiom is a special function that produces
a behavior tree, the function is expected to either take no children, takes
a list of children via parameters "subtrees", or takes a single
child via parameter "behavior". The xml parser will treat children in the
same way that it treats children for all other behaviors. That is the
children should be a subnode of the idiom node.

### Subtrees

Additionally, it is possible to create a [subtree](#sub-trees), where a subtree is an xml
containing a complete behavior tree. This xml file can be included in other xml
files and therefore allows for complete modularity of trees.

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
from py_trees_parser import BTParser
import py_trees
from rclpy import logging

logger = logging.get_logger('parser')
logger.set_level(logging.LoggingSeverity.DEBUG)

# Parse the XML file and create the behavior tree:
xml_file = "behavior_tree.xml"
parser = BTParser(xml_file, logger)
behavior_tree = parser.parse()
```

### Using Your Own Behaviors

The xml parser can use any behavior, whether it is part of `py_trees`, `py_trees_ros`,
or your own python module. The way the parser knows the existence of
the behavior is via the behavior tag in the xml. The behavior tag should be the fully
qualified python path of the behavior, so if you have the following structure of your
python module

```
my_behavior_tree
├── my_behavior_tree
│   ├── __init__.py
│   ├── behaviors
│   │   ├── __init__.py
│   │   └── my_behavior.py
├── package.xml
├── resource
│   └── my_behavior_tree
├── setup.cfg
├── setup.py
└── trees
    ├── my_tree.xml
    ├── subtree2.xml
    └── subtree3.xml
```

then you would include the behaviors in `my_behavior.py` in the following way:

```xml
<my_bhavior_tree.behaviors.my_behavior.MyBehavior name="MyFancyBehavior">
```

The path to this can be shortened by including the class in `__init__.py`.


### Sub-Trees

It is possible to include sub-trees in the xml file containing a behavior tree.
This is made possible via the following:

```xml
<subtree
  name="my_subtree"
  include="/location/of/subtree.xml" />
```

The included subtree should be a complete tree, but can only contain one root.
It is possible to include multiple sub-trees and a sub-tree can also include
another subtree. However, be aware that the all directories are absolute, but it
is possible to use python to determine the path like so:

```xml
<py_trees.composites.Parallel name="Subtree Tutorial" synchronise="False">
    <subtree
      name="my_subtree"
      include="$(os.path.join(ament_index_python.packages.get_package_share_directory('my_package'), 'tree', 'subtree.xml'))" />
</py_trees.composites.Parallel>
```
#### Arguments

It is also possible to use arguments for subtrees. The syntax of which looks like

```xml
<subtree
  name="my_subtree"
  include="/location/of/subtree.xml" >
    <arg name="foo" value="bar" />
</subtree>
```

and then inside the subtree

```xml
<py_trees.composites.Sequence name="Arg Tutorial">
    <py_trees.behaviors.Success name="${foo}" />
</py_trees.composites.Sequence>
```

Furthermore, one can cascade arguments down subtrees using the following syntax:

```xml
<subtree
  name="my_subtree1"
  include="/location/of/subtree1.xml" >
    <arg name="foo" value="bar" />
</subtree>
```

and in subtree1

```xml
<subtree
  name="my_subtree2"
  include="/location/of/subtree2.xml" >
  <arg name="baz" value=${foo}
</subtree>
```

and finally in subtree2

```xml
<py_trees.composites.Sequence name="Cascading Arg Tutorial">
    <py_trees.behaviors.Success name="${baz}" />
</py_trees.composites.Sequence>
```
