import importlib
from xml.etree import ElementInclude, ElementTree


class BTParseError(Exception):
    pass


def is_float(value: str) -> bool:
    # TODO: handle scientific notation
    return value.lstrip("-").replace(".", "", 1).isdigit()


class BTParser:
    def __init__(self, file: str, logger):
        self.file = file
        self.logger = logger

    def _get_handle(self, value: str):
        self.logger.debug("Getting handle")
        if value == "":
            return "", None

        module_name, obj_name = value.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
            handle = getattr(module, obj_name)
        except ModuleNotFoundError:
            module_name, handle = self._get_handle(module_name)
            handle = getattr(handle, obj_name)

        self.logger.info(f"{module_name = }, {obj_name = }, {handle = }")
        return module_name, handle

    def _string_or_num(self, value: str) -> int | float | str:
        value = value.strip()
        if value.isnumeric():
            value = int(value)
        elif is_float(value):
            value = float(value)

        self.logger.debug(f"Found {type(value)} {value = }")

        return value

    def _get_kwargs(self, params: str) -> dict:
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
        # the expectation is that the xml_node will have a tag that is the
        # class and module name as if your were to import the class into
        # python directly
        module_name, class_obj = self._get_handle(node_type)
        self.logger.debug(f"Found {module_name = } and {class_obj = }")
        # name is a special attribute that is handled separately
        name = node_attribs["name"]
        del node_attribs["name"]

        node_attribs = self._convert_attribs(node_attribs)

        self.logger.debug("Creating node")
        if len(children) == 0:
            node = class_obj(name=name, **node_attribs)
        elif "decorators" in module_name:
            node = class_obj(name=name, child=children[0], **node_attribs)
        else:
            node = class_obj(name=name, children=children, **node_attribs)

        return node

    def _build_tree(self, xml_node: ElementTree):
        if xml_node is None:
            self.logger.warn("Received an xml_node of type None this shouldn't happen")
            return None

        self.logger.debug(f"{xml_node.tag = }, {xml_node.attrib = }")

        # we only need to find children if the node is a composite
        children = list()
        for child_xml_node in xml_node:
            child = self._build_tree(child_xml_node)
            children.append(child)

        # build the actual node
        node = self._create_node(xml_node.tag, children, xml_node.attrib)

        return node

    def parse(self):
        xml = ElementTree.parse(self.file)

        ElementInclude.include(xml)

        return self._build_tree(xml.getroot())
