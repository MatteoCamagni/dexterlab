from abc import abstractmethod
from pathlib import Path
from time import sleep
from typing import Any, Dict, List, Tuple

import plantuml
from strenum import StrEnum

from ...types.basic import DlabConnector, Dlabformatter, DlabItem, hash_string

MAPPABLE_FIELDS: list = ["PUML_MAP"]


class PumlNode:

    ITEM_TEMPLATE: str = """
together {{
class "<b>{label}</b>" as {name} << ({symbol},{colour}) {type}>> {{
{description}
{table}
}}

{ports}
}}
"""
    ITEM_FIELD_TEMPLATE: str = "|= {key} | {value} |\n"
    ITEM_PORT_TEMPLATE: str = """
circle "**Port:** {port}" as {port_id}
{port_id} -[dashed] {node_id}
"""

    def __init__(self, group: str = None, **kwargs) -> None:
        self.__kwargs: Dict[str, str] = kwargs
        self.__fields: str = ""
        self.__ports: str = ""
        self.__group: str | None = group

        if "fields" in kwargs:
            for k, v in kwargs.items():
                self.add_field(k, v)

        if "ports" in kwargs:
            for k, v in kwargs.items():
                self.add_port(k, v)

    @property
    def group(self) -> str:
        return self.__group

    def add_field(self, key: str, value: str) -> None:
        self.__fields += self.ITEM_FIELD_TEMPLATE.format(key=key, value=value)

    def add_port(self, port: str, port_id: str, node_id: str) -> None:
        self.__ports += self.ITEM_PORT_TEMPLATE.format(
            port=port, port_id=port_id, node_id=node_id
        )

    def render(self) -> str:
        return self.ITEM_TEMPLATE.format(
            table=self.__fields, ports=self.__ports, **self.__kwargs
        )


class PumlBaseformatter:

    TEMPLATE = """@startuml
'Style
<style>
{style}
</style>

'Default setup
{defs}

'Groups
{groups}

'Free items
{items}

'Free links
{links}

@enduml"""

    def __init__(self, style_content: str = "", setup_defs: str = "") -> None:
        self.__style: str = style_content
        self._free_items: str = ""
        self._free_connectors: str = ""
        self._groups: str = ""
        self._setup_defs: str = setup_defs

    @abstractmethod
    def add_item(self, item: DlabItem) -> str:
        pass

    @abstractmethod
    def add_connection(self, conn: DlabConnector) -> str:
        pass

    @abstractmethod
    def export(self, *args, **kwargs) -> str:
        pass

    @abstractmethod
    def export_as_string(self, *args, **kwargs) -> str:
        pass

    def resolve(self) -> None:
        pass

    @property
    def style_block(self) -> str:
        return self.__style

    def _inner_export_as_string(self, setup_defs: str) -> str:
        self.resolve()
        return self.TEMPLATE.format(
            style=self.__style,
            defs=setup_defs,
            groups=self._groups,
            items=self._free_items,
            links=self._free_connectors,
        )


class DefaultPumlformatter(PumlBaseformatter, Dlabformatter):
    NAME: str = "puml"

    # Init
    INIT_DEFS: str = """header {header}
title {title_label}
allowmixing
skinparam linetype ortho
skinparam nodesep 50
skinparam ranksep 50
"""

    # Item attributes
    ITEM_TEMPLATE: str = """
class "<b>{label}</b>" as {name} << ({symbol},{colour}) {type}>> {{
{description}
{table}
}}
"""
    ITEM_FIELD_TEMPLATE: str = "|= {key} | {value} |\n"
    ITEM_MANDATORY_FIELDS: Tuple = (
        "label",
        "name",
        "type",
        "symbol",
        "colour",
        "description",
    )

    # Connector attributes
    CONNECTOR_TEMPLATE: str = "{start} - {end}\n"

    # Port attributes
    PORT_TEMPLATE = """circle "**Port:** {port}" as {port_id}
{item_id} -[dashed]- {port_id}"""

    # Group attributes
    PKG_TEMPLATE: str = """package "<b>{label}</b>" as {label} {{
{content}
}}
"""

    def __init__(self) -> None:
        # self.__group_handler: Dict[str, str] = {}
        self.__nodes: Dict[str, PumlNode] = {}
        super().__init__()

    def __get_node_uid(self, item: DlabItem, port: str = None) -> str:
        item_uid: str = hash_string(item.uid() + port) if port else item.uid()
        if item.group:
            return f"{item.group}.{item_uid}"
        return item_uid

    def __add_port(self, port_name: str, item: DlabItem) -> None:
        # Add port to the relative node
        node: PumlNode = self.__nodes[item.uid()]
        node.add_port(
            port=port_name,
            port_id=hash_string(item.uid() + port_name),
            node_id=item.uid(),
        )

    def add_item(self, item: DlabItem) -> str:
        puml_map: Dict = {"type": item.__class__.__qualname__}

        # Create map
        for cl in reversed(type(item).__mro__):
            for field in MAPPABLE_FIELDS:
                if field in vars(cl):
                    puml_map.update(getattr(cl, field))

        # Resolve map
        for k, v in puml_map.items():
            new_value: Any | str = getattr(item, v, None)
            if new_value:
                if callable(new_value):
                    new_value = str(new_value())
            else:
                new_value = v
            puml_map[k] = new_value

        # Add a node
        node: PumlNode = PumlNode(group=item.group, **puml_map)

        for k, v in puml_map.items():
            if k not in self.ITEM_MANDATORY_FIELDS:
                node.add_field(key=k.capitalize(), value=v)

        # Store the node
        self.__nodes.update({item.uid(): node})

    def add_connection(self, conn: DlabConnector) -> str:
        # Connector node
        cnt_uid: str = self.__get_node_uid(conn)

        # Start node
        start_node_uid: str = self.__get_node_uid(conn.start_node, conn.start_node_port)
        self.__add_port(port_name=conn.start_node_port, item=conn.start_node)

        # End node
        end_node_uid: str = self.__get_node_uid(conn.end_node, conn.end_node_port)
        self.__add_port(port_name=conn.end_node_port, item=conn.end_node)

        # Links
        self._free_connectors += self.CONNECTOR_TEMPLATE.format(
            start=start_node_uid, end=cnt_uid
        )
        self._free_connectors += self.CONNECTOR_TEMPLATE.format(
            start=cnt_uid, end=end_node_uid
        )

    def resolve(self) -> None:
        self._free_items: str = ""
        self._groups: str = ""
        for node in self.__nodes.values():
            node_render: str = node.render()
            if node.group:
                self._groups += self.PKG_TEMPLATE.format(
                    label=node.group, content=node_render
                )
            else:
                self._free_items = node_render + self._free_items

    def export_as_string(
        self,
        labname: str,
        variant: str | None,
        location: str,
        env: Dict = {},
        description: str = "",
        *args,
        **kwargs,
    ) -> str:
        variant = "" if variant == "" else ":" + variant

        return self._inner_export_as_string(
            setup_defs=self.INIT_DEFS.format(
                header=f"Laboratory location: {location}", title_label=labname + variant
            )
        )

    def export(
        self,
        filename: str,
        labname: str,
        location: str,
        variant: str,
        env: Dict = {},
        description: str = "",
        puml_server: str = "http://www.plantuml.com/plantuml/",
        extension: str = None,
        max_attempts: int = 15,
        attempt_pause: float = 1.0,
        **kwargs,
    ) -> None:
        errors: List = []
        file: Path = Path(filename)

        if extension == None:
            extension = Path(filename).suffix.replace(".", "")

        if extension == "png":
            puml_server += "img/"
        elif extension == "svg":
            puml_server += "svg/"
        else:
            raise Exception("Error: extension not found or supported!")

        if file.suffix == "":
            file.with_suffix(extension)

        server = plantuml.PlantUML(url=puml_server)
        base = self.export_as_string(
            labname=labname,
            variant=variant,
            location=location,
            env=env,
            description=description,
        )
        for _ in range(max_attempts):
            try:
                with file.open("wb") as f:
                    f.write(server.processes(base))
                return
            except Exception as e:
                max_attempts -= 1
                errors.append(str(e))
                sleep(attempt_pause)

        raise Exception(
            f"Error: Maximum attempts number reached [{max_attempts}]! Check the network connectivity or the PlantUML server.\nTraceback:\n"
            + "\n--------\n".join(errors)
        )
