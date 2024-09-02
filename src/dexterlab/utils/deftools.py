from pathlib import Path
from typing import Dict, List

import yaml


class Variant:
    def __init__(self, name: str, **kwargs) -> None:
        self.name: str = name

        # Init attributes
        for k, v in kwargs.items():
            setattr(self, k, v)


class ConfigHandler:
    def __init__(self, config_path: str) -> None:
        self.active_variant: str = None
        self.config_path: Path = Path(config_path)
        self.discovered_plugins: List[str] = []
        self.discovered_variants: Dict[str, Variant] = {}
        self.__registered_variants: List[str] = []
        self.__registered_attributes: List[str] = []

        # Register the representer and constructors with PyYAML
        yaml.add_representer(Variant, self.variant_representer)
        yaml.add_constructor("!variant", self.variant_constructor)
        yaml.add_constructor("!plugin", self.plugin_constructor)
        yaml.add_constructor("!varfield", self.varfield_constructor)

    def variant_representer(self, dumper: yaml.Dumper, data):
        return dumper.represent_formatters("!variant", {"name": data.name})

    def variant_constructor(self, loader, node):
        tmp_values = loader.construct_mapping(node)
        self.__check_variant(values=tmp_values)
        self.discovered_variants.update({tmp_values["name"]: Variant(**tmp_values)})

    def plugin_constructor(self, loader, node):
        self.discovered_plugins.append(node.value)

    def varfield_constructor(self, loader, node):
        if self.active_variant == None:
            raise ValueError(
                "Error: Variant not found, tag interpolaton <!varfield> failed!"
            )
        return getattr(self.discovered_variants[self.active_variant], node.value)

    def __check_variant(self, values: Dict) -> None:
        name = values["name"]
        # Check name
        if name in self.__registered_variants:
            raise ValueError(f"Error: Variant <{name}> already defined!")
        # Register variant
        self.__registered_variants.append(name)

        # Chek attributes
        if not self.__registered_attributes:
            for v in values.keys():
                self.__registered_attributes.append(v)
        else:
            if self.__registered_attributes != list(values.keys()):
                raise ValueError(
                    "Error: all the variants must have the same attributes\n"
                    + f"Registered: {self.__registered_attributes}\n"
                    + f"{name}'s attributes: {list(values.keys())}\n"
                )

    def get_config_dict(self, active_variant: str | None) -> Dict:
        self.active_variant = active_variant

        with self.config_path.open("r") as f:
            for p in yaml.load_all(f, Loader=yaml.FullLoader):
                if any(p):
                    break

        self.active_variant = None
        return p
