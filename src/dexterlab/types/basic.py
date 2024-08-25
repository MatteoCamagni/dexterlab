import hashlib
from abc import ABC, abstractmethod
from enum import Enum
from functools import cache
from typing import Any, Dict, Tuple


@cache
def hash_string(str_in: str) -> str:
    return hashlib.md5(str_in.encode()).hexdigest()


class ConnectorCategory(Enum):
    POWER = 0
    DATAX = 1
    DATAW = 2
    DATAR = 3


class DlabLink:

    PUML_MAP: Dict = {
        "label": "name",
        "Connection Type": "type",
        "symbol": "C",
        "colour": "Grey",
    }

    def __init__(
        self,
        name: "str",
        start: "str",
        end: "str",
        start_port: "str",
        end_port: "str",
        category: str,
        manual_only: bool = False,
        autoconnect: bool = True,
        **kwargs,
    ):
        self.__name: str = name
        self.__start_node_name: str = start
        self.__end_node_name: str = end
        self.start_node: DlabNode = None
        self.end_node: DlabNode = None
        self.__start_node_port: str = start_port
        self.__end_node_port: str = end_port
        self.__category: ConnectorCategory = ConnectorCategory[category]
        self.__manual_only: bool = manual_only
        self.__autoconnect: bool = autoconnect

        super(DlabLink, self).__init__(**kwargs)

    def get_nodes(self) -> Tuple[None | str, None | str]:
        return self.__emitter if isinstance(self.__emitter, str) else None, (
            self.__receiver if isinstance(self.__receiver, str) else None
        )

    def resolve_nodes(self, emitter: Any = None, receiver: Any = None) -> None:
        if emitter:
            self.__emitter = emitter
        if receiver:
            self.__receiver = receiver

    @property
    def name(self) -> str:
        return self.__name

    @property
    def start_node_name(self) -> str:
        return self.__start_node_name

    @property
    def end_node_name(self) -> str:
        return self.__end_node_name

    @property
    def start_node_port(self) -> str:
        return self.__start_node_port

    @property
    def end_node_port(self) -> str:
        return self.__end_node_port

    @property
    def type(self) -> str:
        return self.__category.name

    @property
    def autoconnect(self) -> bool:
        return self.__autoconnect

    @property
    def manual_only(self) -> bool:
        return self.__manual_only


class DlabNode:

    PUML_MAP: Dict = {
        "label": "name",
    }

    def __init__(self, name: str, **kwargs) -> None:
        self.__name: str = name

        super(DlabNode, self).__init__(**kwargs)

    @property
    def name(self) -> str:
        return self.__name


class DlabItem(ABC):

    PUML_MAP: Dict = {
        "Part Number": "part_number",
        "Serial Number": "serial_number",
        "description": "description",
        "symbol": "I",
        "colour": "Green",
    }

    def __init__(
        self, sn: str, pn: str, description: str = None, group: str = None, **kwargs
    ) -> None:
        self.__sn: str = sn
        self.__pn: str = pn
        self.__group: str = group
        self.__description: str = description

        super(DlabItem, self).__init__(**kwargs)

    def __str__(self) -> str:
        res: str = ""
        for k in dir(self):
            v = getattr(self, k)
            if not k.startswith("_") and not callable(v):
                res += f"{k} = {v}\n"

        return res

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def serial_number(self) -> str:
        return self.__sn

    @property
    def part_number(self) -> str:
        return self.__pn

    @property
    def description(self) -> str:
        return self.__description

    @property
    def group(self) -> str:
        return self.__group

    @abstractmethod
    def uid(self) -> str:
        pass


class DlabInstrument(DlabNode, DlabItem):

    PUML_MAP: Dict = {
        "name": "uid",
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    @abstractmethod
    def power_on(self) -> bool:
        pass

    @abstractmethod
    def power_off(self) -> bool:
        pass

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        pass

    def uid(self) -> str:
        return hash_string(self.name + self.serial_number)


class DlabConnector(DlabLink, DlabItem):
    PUML_MAP: Dict = {
        "name": "uid",
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def uid(self) -> str:
        return hash_string(self.name + self.serial_number)


class DlabMapper(ABC):

    def __init__(self) -> None:
        pass
    
    @abstractmethod
    def add_item(self, item: DlabItem) -> str:
        pass

    @abstractmethod
    def add_connection(self, conn: DlabConnector) -> str:
        pass

    @abstractmethod
    def export(
        self,
        filename: str,
        labname: str,
        env: Dict = {},
        description: str = "",
        *args,
        **kwargs,
    ) -> None:
        pass

    @abstractmethod
    def export_as_string(
        self, labname: str, env: Dict = {}, description: str = "", *args, **kwargs
    ) -> str:
        pass
