from pathlib import Path
import yaml
from typing import List, Dict

class Variant:
    
    _registered_variants: List = []
    _reigstered_attributes: List = []
    
    def __init__(self, name:str, **kwargs ) -> None:
        # Check name
        assert name not in self._registered_variants, \
            f"Error: Variant <{name}> already defined!"
        # Register variant
        self._registered_variants.append(name)
        self.name: str = name
        
        # Chek attributes
        if not self._reigstered_attributes:
            for v in kwargs.keys():
                self._reigstered_attributes.append(v)
        else:
            assert self._reigstered_attributes == list(kwargs.keys()), \
                "Error: all the variants must have the same attributes\n" \
                + f"Registered: {self._reigstered_attributes}\n" \
                + f"{name}'s attributes: {list(kwargs.keys())}\n"
            
        # Init attributes
        for k,v in kwargs.items():
            setattr(self,k,v)

class ConfigHandler:
    def __init__(self, config_path: str) -> None:
        self.active_variant: str = None
        self.config_path: Path = Path(config_path)
        self.discovered_plugins: List[str] = []
        self.discovered_variants: Dict[str,Variant] = {}
        
        # Register the representer and constructors with PyYAML
        yaml.add_representer(Variant, self.variant_representer)
        yaml.add_constructor('!variant', self.variant_constructor)
        yaml.add_constructor("!plugin", self.plugin_constructor)
        yaml.add_constructor("!varfield", self.varfield_constructor)

    def variant_representer(self,dumper:yaml.Dumper, data):
        return dumper.represent_mapping('!variant', {'name': data.name})

    def variant_constructor(self,loader, node):
        values = loader.construct_mapping(node)
        self.discovered_variants.update({values['name']:Variant(**values)})

    def plugin_constructor(self,loader, node):
        self.discovered_plugins.append(node.value)

    def varfield_constructor(self, loader, node):
        return getattr(self.discovered_variants[self.active_variant],node.value)
                   

    def get_config_dict(self, active_variant: str) -> Dict:
        self.active_variant = active_variant
        
        with self.config_path.open("r") as f:
            for p in yaml.load_all(f, Loader=yaml.FullLoader):
                if any(p):
                    break
        
        self.active_variant = None
        return p