# Copyright 2025 SAM XL
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

try:
    import rclpy
    from rclpy import logging
except ModuleNotFoundError:
    import logging


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


def is_bool(value: str) -> bool:
    """
    Check if a string is a boolean type, i.e. True or False.

    Args:
    ----
        value: The string to check.

    Returns:
    -------
        True if the string is "true", "True", "false", or "False", False otherwise.

    """
    return value.lower() == "true" or value.lower() == "false"


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


def extract_params(func: str) -> ast.Call | None:
    """
    Extract a list of parameters from a string representing a python function.

    Args:
    ----
       func (str): string representing python function.

    Returns:
    -------
       list(str): list of parameters found.

    Raises:
    ------
       ValueError: if the function call is malformed.

    """
    try:
        # Parse the string into an AST
        tree = ast.parse(func)
    except SyntaxError as ex:
        raise ValueError(f"Couldn't read function parameters: {func}") from ex

    # Find the first function call node in the AST
    call_node = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            call_node = node
            break

    return call_node


def handle_success_on_selected(node_attribs: dict) -> tuple[list[str] | None, bool]:
    """
    Handle the special SuccessOnSelected parameter.

    Args:
    ----
        node_attribs (dict): The attributes of the XML node.

    Returns:
    -------
        A tuple containing the list of children to be selected and the synchronise parameter.

    """
    on_selected = None
    synchronise = None
    if (policy := node_attribs.get("policy")) is not None and "SuccessOnSelected" in policy:
        call_node = extract_params(policy[2:-1])
        if call_node is None:
            raise ValueError(f"Missing parameters for 'SuccessOnSelected': {policy[2:-1]}")

        positional_args = [ast.unparse(arg) for arg in call_node.args]
        keyword_args = {key.arg: ast.unparse(key.value) for key in call_node.keywords}

        if len(positional_args) == 2:
            children_arg = positional_args[0]
            synchronise = positional_args[1].lower() == "true"
        elif len(positional_args) == 1:
            children_arg = positional_args[0]

        for key, value in keyword_args.items():
            if key == "children":
                children_arg = value
            elif key == "synchronise":
                synchronise = value.lower() == "true"

        if children_arg is None:
            raise ValueError(f"No children found in SuccessOnSelected: {policy[2:-1]}")

        # synchronise wasn't set so set it to the default value
        synchronise = True if synchronise is None else synchronise

        start = children_arg.find("[")
        end = children_arg.find("]", start + 1)
        if end == -1:
            raise ValueError(f"Malformed list of children in SuccessOnSelected: {policy[2:-1]}")
        on_selected = [x.strip() for x in children_arg[start + 1 : end].split(",")]

        del node_attribs["policy"]

    return on_selected, synchronise


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
        log_level (optional): The logging level for the parser. This can be
                              rclpy.logging.LoggingSeverity or the log levels from logging.
                              Default logging level is INFO.

    """

    def __init__(
        self,
        file: str,
        log_level: rclpy.logging.LoggingSeverity | int | None = None,
    ):
        """Initialize the BTParser."""
        self.file = file

        try:
            self.logger = logging.get_logger("BTParser")
            self.logger.set_level(
                log_level if log_level is not None else logging.LoggingSeverity.INFO
            )
        except AttributeError:
            formatter = logging.Formatter("[%(levelname)s] [%(name)s] [%(created)f]: %(message)s")
            self.logger = logging.getLogger("BTParser")
            self.logger.setLevel(log_level if log_level is not None else logging.INFO)
            self.logger.setFormatter(formatter)

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
        elif is_bool(value):
            value = value.lower() == "true"
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

        # creating node, so we've handle the condition already
        if "if" in node_attribs:
            del node_attribs["if"]

        self.logger.debug(f"Found {node_type}")

        # handle SuccessOnSelected separately
        on_selected, synchronise = handle_success_on_selected(node_attribs)

        # name is a special attribute that is handled separately
        node_attribs = self._convert_attribs(node_attribs)

        self.logger.debug("Creating node")
        if isinstance(obj, types.FunctionType):
            parameters = inspect.signature(obj).parameters
            if "behaviour" in parameters:
                self.logger.debug("Found behaviour in parameters")
                node = obj(name=name, behaviour=children[0], **node_attribs)
            elif "subtrees" in parameters:
                self.logger.debug("Found subtrees in parameters")
                node = obj(name=name, subtrees=children, **node_attribs)
            elif "tasks" in parameters:
                self.logger.debug("Found tasks in parameters")
                node = obj(name=name, tasks=children, **node_attribs)
            elif len(children) == 0:
                self.logger.debug("No children provided, assuming a behavior")
                node = obj(name=name, **node_attribs)
            else:
                self.logger.error(f"Unknown node type {node_type}")
                raise BTParseError(f"Unknown node type {node_type}")
        elif len(children) == 0:
            self.logger.debug("No children provided, assuming a behavior")
            node = obj(name=name, **node_attribs)
        elif issubclass(obj, py_trees.decorators.Decorator):
            self.logger.debug(f"Found decorator: {node_attribs = }")
            node = obj(name=name, child=children[0], **node_attribs)
        elif on_selected is not None:
            self.logger.debug("Found SuccessOnSelected in parameters")

            selection = [
                child
                for child in children
                if "".join(map(lambda char: char if char.isalnum() else "_", child.name))
                in on_selected
            ]
            if len(selection) == 0:
                raise ValueError("List of children for SuccessOnSelected is empty")

            node = obj(
                name=name,
                children=children,
                policy=py_trees.common.ParallelPolicy.SuccessOnSelected(
                    children=selection, synchronise=synchronise
                ),
            )
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
        if isinstance(var, str) and "${" in var and "}" in var:
            # Handle both full replacement and embedded arguments with the same logic
            result = var
            # Find all ${...} patterns in the string
            start_idx = 0
            while "${" in result[start_idx:]:
                start = result.find("${", start_idx)
                end = result.find("}", start + 2)
                if end == -1:
                    break

                arg_name = result[start + 2 : end]
                if arg_name in args:
                    # Replace the argument with its value
                    result = result[:start] + args[arg_name] + result[end + 1 :]
                    # Start searching from the position after the replacement
                    start_idx = start + len(args[arg_name])
                else:
                    self.logger.error(f"Argument '{arg_name}' not found in arg list: {args}")
                    raise ValueError(f"Argument '{arg_name}' not found in arg list")

            return result

        return None

    def _condition(self, condition):
        if condition is None:
            return True

        try:
            # Safely evaluate the condition
            self.logger.debug(f"Found conditional: {condition}")
            result = eval(condition, {"__builtins__": {}}, {})
            self.logger.debug(f"Condition result: {result}")
            return bool(result)
        except Exception as ex:
            self.logger.error(f"Error evaluating condition '{condition}': {ex}")
            raise ValueError(f"Error evaluating condition '{condition}'") from ex

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
            args (dict[str, str]): Arguments for substitutions in elements, default None.

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
            if_cond = child_xml.attrib.get("if")
            if not self._condition(if_cond):
                continue
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
