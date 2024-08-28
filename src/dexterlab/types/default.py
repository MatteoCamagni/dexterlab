import sys
from pathlib import Path
from importlib import import_module
from typing import List, Set, Union, Any, Callable

from yaml import dump

from ..formatters import DefaultPumlformatter, PlainStringFormatter
from ..validation import default_validator
from .basic import *
from ..utils.deftools import ConfigHandler


class GenericInstrument(DlabInstrument):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def power_on(self) -> bool:
        pass

    def power_off(self) -> bool:
        pass

    def connect(self) -> bool:
        pass

    def disconnect(self) -> bool:
        pass


class CalibratedInstrument(DlabInstrument):
    def __init__(self, calibration_date: str, **kwargs) -> None:
        self.__calibration_date: str = calibration_date
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

    @property
    def calibration_date(self) -> str:
        return self.__calibration_date


class Cable(DlabConnector):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


class Dlab:

    CONNECTOR_BINDER_KEY: str = "item_connector"
    ITEM_NAME_KEY: str = "name"
    NODE_KEYS: Tuple = ("start", "end", "start_port", "end_port")

    def __init__(
        self,
        labdef: str,
        variant: str | None = None,
        classes: Dict[str, Any]| None = None,
        formatters: Dict[str, Dlabformatter]| None = None,
        validator: Callable[[Dict],Tuple[bool,Dict]] = default_validator
    ) -> None:

        # Import lab definition
        tmp_cfg: ConfigHandler = ConfigHandler(config_path=labdef)
        tmp_lab: Dict = tmp_cfg.get_config_dict(active_variant=variant)

        # Validate the lab definition dictionary
        res, errors = validator(labdef=tmp_lab)
        assert res, f"Error: the lab definition is bad formatted.\n{dump(errors)}"

        # Unpack the lab
        self.__name: str = tmp_lab["name"]
        self.__variant: str | None = variant
        self.__description: str = tmp_lab["description"]
        self.__environment: Dict = tmp_lab["environment"]
        self.__location: str = tmp_lab["location"]
        
        # Import plugins
        self.__import_plugins(plugins=tmp_cfg.discovered_plugins)

        # Check input
        self.__check_connections(tmp_lab["connections"])

        # Init attributes
        self.__nodes: List[DlabNode] = []
        self.__links: List[DlabLink] = []
        self.__formatters: Dict[str, Dlabformatter] = None
        self.__classes: Dict[str,Any] = None
        
        # Init classes
        self.__classes = classes if classes else self.__get_classes() 

        # Init formatter objects
        if formatters:
            self.__formatters = {k: v() for k, v in formatters.items()}
        else:
            self.__formatters = self.__get_formatters()
            
        # Resolve topology
        self.__resolve_items(tmp_lab["items"], tmp_lab["connections"])
        self.__update_node_topolgy()

        # Resolve formatters
        self.__update_formatters()

    @property
    def items(self) -> List[Union[DlabNode, DlabItem]]:
        return self.__nodes

    @property
    def connections(self) -> List[Union[DlabLink, DlabItem]]:
        return self.__links

    @property
    def environment(self) -> Dict:
        return self.__environment

    @property
    def formatters(self) -> Dict[str, Dlabformatter]:
        return self.__formatters
    
    @property
    def dexter_classes(self) -> Dict[str, Any]:
        return self.__classes
    
    @property
    def active_variant(self) -> str | None:
        return self.__variant

        
    def __import_plugins(self, plugins: List[str]) -> None:
        for plg in plugins:
            # Try absolute import
            p: Path = Path(plg).absolute()
            if p.exists():
                sys.path.append(str(p.parent))
                plg: str = p.stem
            
            # Finally import it
            import_module(name=plg,package=p.parent)
            
    
    def __get_classes(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        
        # Add instrument classes
        out.update({i_cls.__qualname__ : i_cls for i_cls in DlabInstrument.__subclasses__()})
            
        # Add connector classes
        out.update({c_cls.__qualname__ : c_cls for c_cls in DlabConnector.__subclasses__()})
                
        return out
    
    def __get_formatters(self) -> Dict[str, Dlabformatter]:
        out: Dict[str, Dlabformatter] = {}
        for formatter in Dlabformatter.__subclasses__():
            map_name: str | None = getattr(formatter,"NAME",None)
            if map_name:
                out[map_name] = formatter()
                
        return out

    def __check_connections(self, connections: List) -> None:
        temp_list: Set = set(tuple(v[k] for k in self.NODE_KEYS) for v in connections)
        assert len(temp_list) == len(
            connections
        ), "Error: multiple definitions found for the same connection. Check the connection ports and items."

    def __get_node(self, node_name: str) -> DlabNode:
        for item in self.__nodes:
            if item.name == node_name:
                return item

        raise Exception(f"Error: laboratory item not found <{node_name}>")

    def __get_connection(self, conn_name: str, connections: List) -> Dict:
        for i, x in enumerate(connections):
            if x.get(self.CONNECTOR_BINDER_KEY) == conn_name:
                res: Dict = connections.pop(i)
                del res[self.CONNECTOR_BINDER_KEY]
                return res

        raise Exception(f"Error: connection definition is missing for <{conn_name}>")

    def __resolve_items(self, setup: List, connections: List) -> None:

        for item in setup:
            item_name: str = next(iter(item))
            item_class = self.__classes.get(item_name, None)
            assert (
                item_class != None
            ), f"Error: <{item_name}> is not a valid virtual laboratory class"
            item_value: Dict = item[item_name]
            if issubclass(item_class, DlabNode):
                self.__nodes.append(item_class(**item_value))
            elif issubclass(item_class, DlabLink):
                cnt_dict: Dict = self.__get_connection(
                    item_value.get(self.ITEM_NAME_KEY), connections
                )
                self.__links.append(item_class(**{**item_value, **cnt_dict}))

    def __update_node_topolgy(self) -> None:
        for link in self.__links:
            # Update start node
            link.start_node = self.__get_node(link.start_node_name)

            # Update end node
            link.end_node = self.__get_node(link.end_node_name)

    def __update_formatters(self) -> None:
        for item in self.items + self.connections:
            for map_key in self.__formatters.keys():
                self.__formatters[map_key].add_item(item)
                if isinstance(item, DlabLink):
                    self.__formatters[map_key].add_connection(item)

    def __get_variant_repr(self) -> str:
        return self.__variant if self.__variant else ''

    def to_string(self, formatter: str) -> str:
        return self.__formatters[formatter].export_as_string(
            labname=self.__name, variant=self.__get_variant_repr(), location=self.__location, env=self.__environment, description=self.__description
        )

    def export(self, formatter: str, filename: str, **kwargs) -> None:
        self.__formatters[formatter].export(
            filename=filename,
            variant=self.__get_variant_repr(),
            location=self.__location,
            labname=self.__name,
            env=self.__environment,
            description=self.__description,
            **kwargs,
        )
