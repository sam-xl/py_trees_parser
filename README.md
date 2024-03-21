# Behavior Tree
This is the Thermoplast behavior tree module. It contains behaviors that are developed for this project but could be reusable in other applications.

## Dependencies
* ros-humble
* ros-humble-py-trees
* ros-humble-py-trees-ros-interfaces
* ros-humble-py-trees-ros

## Behaviors
* `image_subscriber` ([py_trees_ros.subscribers.ToBlackboard]): Subscribe to the Image message and write an Image (sensor_msgs/Image) to the blackboard.
### Inspection tree behaviors
* `get_image` ([py_trees_ros.actions.ActionClient]): Send an action goal to ([capture_image]) action server.
* `inspect_damage` ([py_trees_ros.actions.ActionClient]): Send an action goal to ([damage_inspection]) action server.
* `pause` ([py_trees.timers.Timer]): A blocking timer behavior.

## Parsing
py-trees-render -b behavior_tree.inspection_tree.inspection_create_root

<!-- links -->
[py_trees_ros.subscribers.ToBlackboard]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#py_trees_ros.subscribers.ToBlackboard
[py_trees_ros.actions.ActionClient]: https://py-trees-ros.readthedocs.io/en/devel/modules.html#module-py_trees_ros.action_clients
[capture_image]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/SaveImage.action?ref_type=heads
[damage_inspection]: https://gitlab.tudelft.nl/samxl/projects/22ind01-rdm-thermoplast/damage_inspection/-/blob/ORTHO-161/Change_damage_inspection_service_to_an_action_server/damage_inspection_msgs/action/DetectDamage.action?ref_type=heads
[py_trees.timers.Timer]: https://py-trees.readthedocs.io/en/release-2.2.x/modules.html#py_trees.timers.Timer