Changelog for package py_trees_parser

.. This is only a rough description of the main changes of the repository
0.6.0 (2025-01-24)
------------------
* Split py_trees_parser out into its own repo

0.5.0 (2024-10-14)
------------------
* Use `args` in subtrees

0.4.0 (2024-09-18)
------------------
* Make `ImageDict` more encapsulated, by adding setters and getters
* Remove Thermoplast specific sensors from `ImageDict`
* Generalize `Robot._sensors` and its subscriptions
* Generalize `Robot._triggers` and its services
* Fix bug in `camera_info` subscription that used wrong data type
* Improve encapsulation of Robot

0.3.0 (2024-09-03)
------------------
* Added support for idioms
* Added support for code in behavior parameters

0.2.0 (2024-08-16)
------------------
* Bump version
* Add `Changelog`

0.1.7 (2024-08-14)
------------------
* Add Joint motion behaviors: `MoveToNamedTarget` and `MoveJoint`
* Create `Pick and Place` pipeline

0.1.4 (2024-08-02)
------------------
* Add a `RepeatFromBlackboard` Behavior

0.1.2 (2024-07-24)
------------------
* Add a `SetABBIOSignal` Behavior

0.1.0 (2024-07-23)
------------------
* Create a cartesian motion behavior `MoveCartesian`

0.0.3 (2024-07-03)
------------------
* Add the ability to include subtrees

0.0.2 (2024-04-02)
------------------
* First release of behavior_tree
