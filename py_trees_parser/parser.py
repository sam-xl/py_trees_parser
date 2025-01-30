# Copyright 2025 SAM-XL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for parsing behavior tree XML files.

This module contains the `BTParser` class, which is used to parse behavior tree XML files.

The `BTParser` class has the following methods:
"""

import ast
import importlib
import inspect
import types
from typing import Any
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

import py_trees
import rclpy
from rclpy import logging


class BTParseError(Exception):
    """Exception raised when there is an error parsing a behavior tree."""

    pass


def is_float(value: str) -> bool:
    """
    Check if a string can be converted to a float.

    Args:
    ----
        value: The string to check.

    Returns:
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
    Check if a string is intended to be code.

    This will check if a string is surrounded by $(), which indicates it is intended to be code.

    Args:
    ----
        value: The string to check.

    Returns:
    -------
        True if the string represents code, False otherwise.

    """
    return value.startswith("$(") and value.endswith(")")


def is_arg(value: str) -> bool:
    """
    Check if a string is intended to be an argument.

    This will check if a string is surrounded by ${}, which indicates it is intended to be an
    argument.

    Args:
    ----
        value: The string to check.

    Returns:
    -------
        True if the string represents an argument, False otherwise.

    """
    return value.startswith("${") and value.endswith("}")


def extract_modules(ast_tree: ast.AST) -> list[str]:
    """
    Extract module and submodules from the input AST.

    Args:
    ----
        ast_tree (ast.AST): The abstract syntax tree parsed from the input string.

    Returns:
    -------
        list[str]: A list of strings, where each string represents a module or submodule.

    """
    modules = set()

    def extract_module_names(node):
        if isinstance(node, ast.Attribute):
            # Extract module names from attribute access (e.g., my_module.submodule)
            module_name = []
            current_node = node
            while isinstance(current_node, ast.Attribute):
                module_name.append(current_node.attr)
                current_node = current_node.value
            if isinstance(current_node, ast.Name):
                module_name.append(current_node.id)
            modules.add(".".join(reversed(module_name)))
        elif isinstance(node, ast.Name):
            # Extract module names from simple names (e.g., my_module)
            modules.add(node.id)
        elif isinstance(node, ast.Call):
            # Recursively extract module names from function calls
            extract_module_names(node.func)
        elif isinstance(node, ast.Subscript):
            # Recursively extract module names from subscript expressions
            extract_module_names(node.value)

    for node in ast.walk(ast_tree):
        extract_module_names(node)

    return list(modules)


class BTParser:
    """
    A parser for behavior trees.

    This class takes an XML file and a dictionary of behavior tree classes,
    and uses them to construct a behavior tree.

    Attributes:
    ----------
        file (str): The XML file to parse.
        logger (logging.Logger): A logger for debugging and error messages.

    Args:
    ----
        file (str): The XML file to parse.
        log_level (logging.LoggingSeverity, optional): The logging level for the parser.

    """

    def __init__(
        self,
        file: str,
        log_level: logging.LoggingSeverity = logging.LoggingSeverity.INFO,
    ):
        """Initialize the BTParser."""
        self.file = file

        self.logger = rclpy.logging.get_logger("BTParser")
        self.logger.set_level(log_level)

    def _get_handle(self, value: str) -> tuple[str, Any]:
        """
        Retrieve a handle (i.e., a module or function) from a string.

        Args:
        ----
            value (str): The string to retrieve the handle from.

        Returns:
        -------
            A tuple containing the module name and the handle.

        Raises:
        ------
            KeyError: If the node_type is not an expected type.

        """
        self.logger.debug(f"Getting handle: {value}")
        if value == "":
            return "", None

        try:
            module_name, obj_name = value.rsplit(".", 1)
        except ValueError as ex:
            raise KeyError("Error parsing handle") from ex

        try:
            module = importlib.import_module(module_name)
            handle = getattr(module, obj_name)
        except ModuleNotFoundError:
            module_name, handle = self._get_handle(module_name)
            handle = getattr(handle, obj_name)

        self.logger.debug(f"{module_name = }, {obj_name = }, {handle = }")
        return module_name, handle

    def _parse_code(self, value: str) -> Any:
        code_block = value[2:-1]
        self.logger.debug(f"Parsing code: {code_block}")
        expr = ast.parse(code_block, mode="eval")
        self.logger.debug(ast.dump(expr))
        modules_to_import = extract_modules(expr)
        self.logger.debug(f"{modules_to_import = }")
        for module in modules_to_import:
            if module not in globals():
                try:
                    globals()[module] = importlib.import_module(module)
                except ImportError:
                    self.logger.debug(f"Assuming {module} is a variable")

        try:
            value = eval(compile(expr, "<string>", "eval"))
        except AttributeError as ex:
            self.logger.error(f"Evaluation of {code_block = } failed: {ex}")
            raise ex

        return value

    def _string_num_or_code(self, value: str) -> Any:
        """
        Convert a string to either an integer, float, code, or leave it as a string.

        Args:
        ----
            value: The string to convert.

        Returns:
        -------
            The converted value.

        """
        value = value.strip()
        if value.isnumeric():
            value = int(value)
        elif is_float(value):
            value = float(value)
        elif is_code(value):
            value = self._parse_code(value)

        self.logger.debug(f"Found {type(value)} {value = }")

        return value

    def _get_kwargs(self, params: str) -> dict:
        """
        Retrieve keyword arguments from a string.

        Args:
        ----
            params (str): The string to retrieve keyword arguments from.

        Returns:
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

        Returns:
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

    def _create_node(
        self, node_type: str, children: list, node_attribs: dict
    ) -> py_trees.behaviour.Behaviour:
        """
        Create a node in the behavior tree.

        Args:
        ----
            node_type (str): The type of the node.
            children (list): A list of child nodes.
            node_attribs (dict): A dictionary of node attributes.

        Returns:
        -------
            The created node.

        Raises:
        ------
            KeyError: If the node_type is not an expected type.
            BTParseError: If the parsed obj cannot be parsed correctly.

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
                f"{node_type = } was not an expected type (Behavior, Composite, Decorator, Idiom)"
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

    def _process_args(self, xml_node: Element, args: dict) -> None:
        """
        Substitute arguments in the subtree.

        Args:
        ----
            xml_node (Element): The XML node to substitute arguments in.
            args (dict[str, str]): Arguments to substitute in the subtree.

        """
        if len(args) == 0:
            return

        for attr_name, attr_value in list(xml_node.attrib.items()):
            arg_value = self._sub_args(args, attr_value)
            if arg_value is not None:
                self.logger.debug(f"Substituting {attr_value} with {arg_value}")
                xml_node.set(attr_name, arg_value)

    def _sub_args(self, args, var):
        if is_arg(var):
            var_name = var[2:-1]
            if var_name in args:
                return args[var_name]
            else:
                self.logger.error(f"Argument '{var_name}' not found in arg list: {args}")
                raise ValueError(f"Argument '{var_name}' not found in arg list")

        return None

    def _build_tree(
        self,
        xml_node: Element,
        args: dict | None = None,
    ) -> py_trees.behaviour.Behaviour:
        """
        Build the behavior tree from an XML node.

        Args:
        ----
            xml_node (Element): The XML node to build the tree from.
            args (dict[tuple[str, str]]): Arguments for substitutions in elements, default None.

        Returns:
        -------
            The built behavior tree.

        """
        if args is None:
            args = {}
        else:
            self.logger.debug(f"{args = }")

        if xml_node is None:
            self.logger.warn("Received an xml_node of type None this shouldn't happen")
            return None

        self._process_args(xml_node, args)

        if xml_node.tag.lower() == "subtree":
            subtree_name = xml_node.attrib.get("name")
            include = self._string_num_or_code(xml_node.attrib.get("include"))
            self.logger.debug(f"Found subtree: {subtree_name}, {include}")
            new_args = {}
            for child_xml in xml_node:
                if child_xml.tag.lower() == "arg":  # create argument dict
                    self._process_args(child_xml, args)
                    name = child_xml.attrib.get("name")
                    new_args[name] = child_xml.attrib.get("value")
                    self.logger.debug(f"Found arg: {name} = {new_args[name]}")
                else:  # no more args so parse subtree
                    raise AttributeError(
                        f"Unexpected tag in subtree ({subtree_name}): {child_xml.tag.lower()}"
                    )
            return self._build_tree(self._get_xml(include), {**args, **new_args})

        # we only need to find children if the node is a composite
        children = list()
        for child_xml in xml_node:
            self._process_args(child_xml, args)
            child = self._build_tree(child_xml, args)
            children.append(child)

        # build the actual node
        node = self._create_node(xml_node.tag, children, xml_node.attrib)

        return node

    def _get_xml(self, file) -> Element:
        """
        Load the XML file as an ElementTree.

        Args:
        ----
            file (str): The path to the XML file.

        Returns:
        -------
            The root element of the XML file.

        Raises:
        ------
            FileNotFoundError: If the XML file cannot be found.

        """
        try:
            with open(file) as f:
                xml_str = f.read()
        except FileNotFoundError as ex:
            self.logger.error(f"XML file {file} not found")
            raise FileNotFoundError(f"XML file {file} not found") from ex

        root = ElementTree.fromstring(xml_str)
        return root

    def parse(self) -> py_trees.behaviour.Behaviour:
        """
        Parse the XML file and build the behavior tree.

        Returns:
        -------
            The built behavior tree.

        """
        root = self._get_xml(self.file)

        return self._build_tree(root)
