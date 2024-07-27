import importlib
from xml.etree import ElementInclude, ElementTree

import py_trees
import rclpy


class BTParseError(Exception):
    """Exception raised when there is an error parsing a behavior tree."""

    pass


def is_float(value: str) -> bool:
    """
    Check if a string can be converted to a float.

    Args:
    ----
        value: The string to check.

    Returns
    -------
        True if the string can be converted to a float, False otherwise.

    """
    # TODO: handle scientific notation
    return value.lstrip("-").replace(".", "", 1).isdigit()


class BTParser:
    """
    A parser for behavior trees.

    This class takes an XML file and a dictionary of behavior tree classes,
    and uses them to construct a behavior tree.

    Attributes
    ----------
        file (str): The XML file to parse.
        logger (logging.Logger): A logger for debugging and error messages.

    Args:
    ----
        file (str): The XML file to parse.

    """

    def __init__(self, file: str):
        self.file = file

        self.logger = rclpy.logging.get_logger("BTParser")

    def _get_handle(self, value: str):
        """
        Retrieve a handle (i.e., a module or function) from a string.

        Args:
        ----
            value (str): The string to retrieve the handle from.

        Returns
        -------
            A tuple containing the module name and the handle.

        """
        self.logger.debug(f"Getting handle: {value}")
        if value == "":
            return "", None

        try:
            module_name, obj_name = value.rsplit(".", 1)
        except Exception as ex:
            raise KeyError(f"Error parsing handle: {ex}")

        try:
            module = importlib.import_module(module_name)
            handle = getattr(module, obj_name)
        except ModuleNotFoundError:
            module_name, handle = self._get_handle(module_name)
            handle = getattr(handle, obj_name)

        self.logger.debug(f"{module_name = }, {obj_name = }, {handle = }")
        return module_name, handle

    def _string_or_num(self, value: str) -> int | float | str:
        """
        Convert a string to either an integer, float, or leaves it as a string.

        Args:
        ----
            value: The string to convert.

        Returns
        -------
            The converted value.

        """
        value = value.strip()
        if value.isnumeric():
            value = int(value)
        elif is_float(value):
            value = float(value)

        self.logger.debug(f"Found {type(value)} {value = }")

        return value

    def _get_kwargs(self, params: str) -> dict:
        """
        Retrieve keyword arguments from a string.

        Args:
        ----
            params (str): The string to retrieve keyword arguments from.

        Returns
        -------
            A dictionary of keyword arguments.

        """
        kwargs = dict()
        try:
            for item in params.split(","):
                if len(item) == 0:
                    continue

                key, value = item.split("=")
                value = self._string_or_num(value)

                kwargs[key.strip()] = value

        except Exception as ex:
            self.logger.error(f"Parameters {kwargs} is invalid: {ex}")

        self.logger.debug(f"Found {kwargs = }")

        return kwargs

    def _convert_attribs(self, node_attribs: dict) -> dict:
        """
        Convert the attributes of an XML node to a dictionary.

        Args:
        ----
            node_attribs (dict): The attributes of the XML node.

        Returns
        -------
            A dictionary of converted attributes.

        """
        if node_attribs is None:
            return None

        self.logger.debug("Converting attributes")
        for key, value in node_attribs.items():
            value = self._string_or_num(value)
            if not isinstance(value, str):
                node_attribs[key] = value
                continue

            try:
                # check if the value is a function call
                if "(" in value:
                    self.logger.debug(f"Possible function {value}")
                    func, params = value.rsplit("(", 1)
                    params = params[:-1]  # remove final parenthesis
                    # get the function handle
                    _, handle = self._get_handle(func)
                    self.logger.debug(f"{handle = }")
                    # remove trailing ) and convert to a dict
                    kwargs = self._get_kwargs(params[:-1])
                    # evaluate the function
                    if len(kwargs) > 0:
                        self.logger.debug(f"Calling {handle = } with {kwargs = }")
                        node_attribs[key] = handle(**kwargs)
                    else:
                        self.logger.debug(f"Calling {handle = } with no args")
                        node_attribs[key] = handle()
                    self.logger.debug(f"Found function {func}")
                else:
                    self.logger.debug(f"Checking for handle {value}")
                    _, handle = self._get_handle(value)
                    node_attribs[key] = handle
                    self.logger.debug(f"Found handle {value}")
            except Exception as ex:
                self.logger.debug(f"No handle or function associated with {value}")
                self.logger.debug(f"{ex}")
                continue

        return node_attribs

    def _create_node(self, node_type: str, children: list, node_attribs: dict):
        """
        Create a node in the behavior tree.

        Args:
        ----
            node_type (str): The type of the node.
            children (list): A list of child nodes.
            node_attribs (dict): A dictionary of node attributes.

        Returns
        -------
            The created node.

        Raises
        ------
            KeyError: If the node_type is not an expected type.

        """
        # the expectation is that the xml_node will have a tag that is the
        # class and module name as if your were to import the class into
        # python directly
        module_name, class_obj = self._get_handle(node_type)

        if not (
            issubclass(class_obj, py_trees.behaviour.Behaviour)
            or issubclass(class_obj, py_trees.composites.Composite)
            or issubclass(class_obj, py_trees.decorators.Decorator)
        ):
            raise KeyError(
                f"{node_type = } was not an expected type (Behavior, Composite, Decorator)"
            )

        self.logger.debug(f"Found {module_name = } and {class_obj = }")
        # name is a special attribute that is handled separately
        name = node_attribs["name"]
        del node_attribs["name"]

        self.logger.debug(f"Found {node_type}")

        # name is a special attribute that is handled separately
        node_attribs = self._convert_attribs(node_attribs)

        self.logger.debug("Creating node")
        if len(children) == 0:
            node = class_obj(name=name, **node_attribs)
        elif issubclass(class_obj, py_trees.decorators.Decorator):
            node = class_obj(name=name, child=children[0], **node_attribs)
        else:
            node = class_obj(name=name, children=children, **node_attribs)

        return node

    def _build_tree(self, xml_node: ElementTree):
        """
        Build the behavior tree from an XML node.

        Args:
        ----
            xml_node (ElementTree): The XML node to build the tree from.

        Returns
        -------
            The built behavior tree.

        """
        if xml_node is None:
            self.logger.warn("Received an xml_node of type None this shouldn't happen")
            return None

        self.logger.debug(f"{xml_node.tag = }, {xml_node.attrib = }")

        if xml_node.tag.lower() == "subtree":
            self.logger.debug("Found subtree")
            return self._build_tree(xml_node[0])

        # we only need to find children if the node is a composite
        children = list()
        for child_xml_node in xml_node:
            child = self._build_tree(child_xml_node)
            children.append(child)

        # build the actual node
        node = self._create_node(xml_node.tag, children, xml_node.attrib)

        return node

    def parse(self):
        """
        Parse the XML file and build the behavior tree.

        Returns
        -------
            The built behavior tree.

        """
        xml = ElementTree.parse(self.file)

        root = xml.getroot()
        ElementInclude.include(root, base_url=self.file)

        return self._build_tree(root)
