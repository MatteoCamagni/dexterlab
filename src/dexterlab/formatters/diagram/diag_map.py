from typing import Dict
from os.path import splitext

from ...types.basic import DlabConnector, Dlabformatter, DlabItem, DlabLink
from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import EC2


# The `DiagramFormatter` class is a Python class that helps format and export diagrams with items and
# connections based on provided information.
class DiagramFormatter(Dlabformatter):
    NAME: str = "diag"
    HEADER: str = """with Diagram('{labname}', show=False, direction='TB', filename='{filename}'):
# Items
{items}

# Connections
{conns}"""

    def __init__(self, _complete: bool = False) -> None:
        self.__conns_code: str = ""
        self.__groups: Dict[str, str] = {None: ""}
        self.__provide_complete_info: bool = _complete

    @staticmethod
    def str_primer(raw_str: str) -> str:
        # TODO: Implement / Override a primer formatter if needed
        return raw_str

    @staticmethod
    def title_primer(raw_str: str) -> str:
        return raw_str.replace("_", " ")

    def __get_items_code(self) -> str:
        ret: str = ""
        for k, v in self.__groups.items():
            if k:
                ret += f"""\n\twith Cluster("{k}"):"""
            ret += v
        return ret

    def __get_code(self, **kwargs) -> str:
        return format(self.str_primer(self.HEADER.format(**kwargs)))

    def add_item(self, item: DlabItem) -> str:
        if not isinstance(item, DlabLink):
            label: str = f"{item.name}"

            if self.__provide_complete_info:
                label += f"""\\nPN: {item.part_number}\\nSN: {item.serial_number}"""

            if item.group not in self.__groups:
                self.__groups[item.group] = ""

            tabbing: str = "\t" * 2 if item.group else "\t"

            self.__groups[item.group] += f"""\n{tabbing}i_{item.uid()}=EC2("{label}")"""

    def add_connection(self, conn: DlabConnector) -> str:
        label: str = f"{conn.name}"

        if self.__provide_complete_info:
            label += f"""\\nPN: {conn.part_number}\\nSN: {conn.serial_number}"""
        self.__conns_code += f"""\n\ti_{conn.start_node.uid()}>>Edge(label="{label}")>>i_{conn.end_node.uid()}"""

    def export(
        self,
        filename: str,
        labname: str,
        variant: str | None,
        env: Dict = {},
        description: str = "",
        *args,
        **kwargs,
    ) -> None:
        filename = splitext(filename)[0]
        exec(
            self.__get_code(
                labname=self.title_primer(labname),
                filename=filename,
                items=self.__get_items_code(),
                conns=self.__conns_code,
            )
        )

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
        return self.__get_code(
            labname=self.title_primer(labname),
            filename="dummy.png",
            items=self.__get_items_code(),
            conns=self.__conns_code,
        )
