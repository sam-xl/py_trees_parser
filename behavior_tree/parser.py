from os.path import isfile

import importlib
import py_trees
from xml.etree import ElementTree
from rclpy import logging


class BTParseError(Exception):
    pass


class BTParser:
    def __init__(self, file: str, logger):
        self.file = file
        self.logger = logger

    def create_node(self, node_type: str, node_attribs):
        # the expectation is that the xml_node will have a tag that is the
        # class and module name as if your were to import the class into
        # python directly
        module_name, class_name = node_type.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_obj = getattr(module, class_name)
        name = node_attribs["name"]
        del node_attribs["name"]

        # TODO: generalize this to all policies in py_trees.common
        if "synchronise" in node_attribs:
            synchronise = node_attribs["synchronise"] == "True"
            del node_attribs["synchronise"]

            node_attribs["policy"] = py_trees.common.ParallelPolicy.SuccessOnAll(
                synchronise=synchronise
            )

        node = class_obj(name=name, **node_attribs)

        return node

    def _build_tree(self, xml_node: ElementTree):
        if xml_node == None:
            self.logger.warn("Received an xml_node of type None this shouldn't happen")
            return None

        self.logger.debug(f"{xml_node.tag = }, {xml_node.attrib = }")

        # build the actual node
        node = self.create_node(xml_node.tag, xml_node.attrib)

        # we only need to find children if the node is a composite
        if isinstance(node, py_trees.composites.Composite) :
            for child_xml_node in xml_node:
                child = self._build_tree(child_xml_node)
                node.add_child(child)

        return node

    def parse(self):
        if isfile(self.file):
            xml = ElementTree.parse(self.file)
        else:
            xml = ElementTree.fromstring(self.file)

        return self._build_tree(xml)
