import ast
import importlib
import inspect
import types
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
    try:
        float(value)
        return True
    except ValueError:
        return False


def is_code(value: str) -> bool:
    """
    Check if a is intended to be code.

    This will check if a string is surrounded by $(), which indicates it is intended to be code.

    Args:
    ----
        value: The string to check.

    Returns
    -------
        True if the string represents code, False otherwise.

    """
    return value.startswith("$(") and value.endswith(")")


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
        except ValueError as ex:
            raise KeyError(f"Error parsing handle: {ex}")

        try:
            module = importlib.import_module(module_name)
            handle = getattr(module, obj_name)
        except ModuleNotFoundError:
            module_name, handle = self._get_handle(module_name)
            handle = getattr(handle, obj_name)

        self.logger.debug(f"{module_name = }, {obj_name = }, {handle = }")
        return module_name, handle

    def _string_num_or_code(self, value: str) -> int | float | str:
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
        elif is_code(value):
            code_block = value[2:-1]
            expr = ast.parse(code_block, mode="eval")
            modules_to_import = [node.id for node in ast.walk(expr) if isinstance(node, ast.Name)]
            for module in modules_to_import:
                if module not in globals():
                    try:
                        globals()[module] = importlib.import_module(module)
                    except ImportError:
                        self.logger.debug(f"Assuming {module} is a variable")
            value = eval(compile(expr, "<string>", "eval"))

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
                value = self._string_num_or_code(value)

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
            value = self._string_num_or_code(value)
            node_attribs[key] = value

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
        module_name, obj = self._get_handle(node_type)

        if not isinstance(obj, types.FunctionType) and not (
            issubclass(obj, py_trees.behaviour.Behaviour)
            or issubclass(obj, py_trees.composites.Composite)
            or issubclass(obj, py_trees.decorators.Decorator)
        ):
            raise KeyError(
                f"{node_type = } was not an expected type (Behavior, Composite, Decorator)"
            )

        self.logger.debug(f"Found {module_name = } and {obj = }")
        # name is a special attribute that is handled separately
        name = node_attribs["name"]
        del node_attribs["name"]

        self.logger.debug(f"Found {node_type}")

        # name is a special attribute that is handled separately
        node_attribs = self._convert_attribs(node_attribs)

        self.logger.debug("Creating node")
        if isinstance(obj, types.FunctionType):
            parameters = inspect.signature(obj).parameters
            if "behaviour" in parameters:
                node = obj(name=name, behaviour=children[0], **node_attribs)
            elif "subtrees" in parameters:
                node = obj(name=name, subtrees=children, **node_attribs)
            elif "tasks" in parameters:
                node = obj(name=name, tasks=children, **node_attribs)
            elif len(children) == 0:
                node = obj(name=name, **node_attribs)
            else:
                self.logger.error(f"Unknown node type {node_type}")
                raise BTParseError(f"Unknown node type {node_type}")

        elif len(children) == 0:
            node = obj(name=name, **node_attribs)
        elif issubclass(obj, py_trees.decorators.Decorator):
            self.logger.debug(f"{node_attribs = }")
            node = obj(name=name, child=children[0], **node_attribs)
        else:
            node = obj(name=name, children=children, **node_attribs)

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
