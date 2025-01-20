# py_trees Parser

This is a xml parser for processing and building a py_trees behavior tree. The
hope is that most if not all capabilities of py_trees will be available for xml
parsing. As such, a py_trees behavior tree will be able to be created by simply
creating an xml file.

## Dependencies

- ElementTree
- ros-humble
- ros-humble-py-trees
- ros-humble-py-trees-ros

To install dependencies you can run the following commands:

```shell
vcs import src < src/behavior_tree/dependencies.repos
rosdep update
rosdep -q install --from-paths src/ --ignore-src -y --rosdistro "${ROS_DISTRO}"
```

where `ROS_DISTRO` is an environment variable containing the ros2 distribution
name.

## XML Parser

The Behavior Tree Parser (`BTParse`) is a Python module that allows you to
parse an XML file representing a behavior tree and construct the corresponding
behavior tree using the `py_trees` library. It supports composite nodes, behavior
nodes from `py_trees`, and custom behavior nodes defined in your local library.

For any parameter that is python code, the code must be surrounded by `$()`.
This allows the parser know that the following parameter value is in fact code
and should be evaluated as code.

Idioms are also now supported. An idiom is a special function that produces
a behavior tree, the function is expected to either take no children, takes
a list of children via parameters "subtrees", or takes a single
child via parameter "behavior". The xml parser will treat children in the
same way that it treats children for all other behaviors. That is the
children should be a subnode of the idiom node.

Additionally, it is possible to create a subtree, where a subtree is an xml
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
`behavior_tree`, or your own python module. The way the parser knows the existance of
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

#### Arguments

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

Furthermore, one can cascade arguments down subtrees using the following syntax:

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <arg name="foo" value="bar" />
    <xi:include href="subtree/subtree1.xml" parse="xml" />
</subtree>
```

with subtree1

```xml
<subtree xmlns:xi="http://www.w3.org/2001/XInclude">
    <arg name="baz" value=${foo}
    <xi:include href="subtree/subtree2.xml" parse="xml" />
</subtree>
```

and finally, subtree2

```xml
<py_trees.composites.Sequence name="Cascading Arg Tutorial">
    <py_trees.behaviors.Success name="${baz}" />
</py_trees.composites.Sequence>
```
