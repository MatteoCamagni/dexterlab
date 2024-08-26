from functools import cache
from pathlib import Path
from typing import Dict

from dexterlab.types.basic import DlabConnector, DlabInstrument

from ...types.basic import ConnectorCategory, DlabItem, DlabMapper

CONNECTION_MAP: Dict = {
    ConnectorCategory.POWER.name: "---",
    ConnectorCategory.DATAR.name: "<--",
    ConnectorCategory.DATAW.name: "-->",
    ConnectorCategory.DATAX.name: "<->",
}


class StringFormatter(DlabMapper):
    NAME: str = "strf"

    DOC_SKELETON: str = """
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
LABORATORY: {labname}
Location: {location}
{descr}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-- Required Environment{environment}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-- Laboratory Items
{items}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|-- Laboratory Connections
{connections}~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

    ROW_SKELETON: str = """
{pipes}|-- {key:<15} : {val}"""

    ELEM_SKELETON: str = """|   |   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|   |-- <<{item_type}>>: {item_name}
|   |   {descr}{rows}
|   |
"""

    CONN_SKELETON: str = """|   |   ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
|   |-- <<{conn_type}>>: {conn_name}
|   |   {start} [{start_port}] {arrow} {end} [{end_port}]
|   |
"""

    def __init__(self) -> None:
        self.__items: str = ""
        self.__connections: str = ""

        super().__init__()

    def add_item(self, item: DlabInstrument) -> None:
        custom_rows: str = ""
        custom_rows += self.ROW_SKELETON.format(
            pipes="|   " * 2, key="Part Number", val=item.part_number
        )
        custom_rows += self.ROW_SKELETON.format(
            pipes="|   " * 2, key="Serial Number", val=item.serial_number
        )

        self.__items += self.ELEM_SKELETON.format(
            item_type=item.__class__.__qualname__,
            item_name=item.name,
            descr=item.description,
            rows=custom_rows,
        )

    def add_connection(self, conn: DlabConnector) -> str:
        self.__connections += self.CONN_SKELETON.format(
            conn_type=conn.__class__.__qualname__,
            conn_name=conn.name,
            start=conn.start_node_name,
            start_port=conn.start_node_port,
            arrow=CONNECTION_MAP[conn.type],
            end=conn.end_node_name,
            end_port=conn.end_node_port,
        )

    def export_as_string(self, labname: str, location: str, env: dict, description: str) -> str:
        if env:
            env_str: str = ""
            for k, v in env.items():
                env_str += self.ROW_SKELETON.format(pipes="|   ", key=k, val=v)
        else:
            env_str: str = "Not required"

        return self.DOC_SKELETON.format(
            labname=labname,
            location=location,
            descr=description,
            environment=env_str,
            items=self.__items,
            connections=self.__connections,
        )

    def export(self, filename: str, extension: str = "txt", **kwargs) -> str:
        p: Path = Path(filename)

        if p.suffix == "":
            # Add extension
            p.with_suffix(extension)

        with p.open("w") as f:
            f.write(self.export_as_string(**kwargs))
