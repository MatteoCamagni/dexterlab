from anytree import Node, RenderTree
from ..types.basic import Dlabformatter, DlabInstrument, DlabConnector
from typing import Any

def _create_discovery_subtree(basenode: Node, baseclass: Any)  -> None:
    for disc in baseclass.__subclasses__():
        Node(name=disc.__qualname__, parent=basenode)
    
def get_cli_discoveries() -> str:
    res: str = ""
    root: Node = Node(name="Dexterlab collection:")
    instr: Node = Node(name="Items:", parent=root)
    connectors: Node = Node(name="Connectors:", parent=root)
    formatters: Node = Node(name="formatters:", parent=root)
    
    _create_discovery_subtree(basenode=instr,baseclass=DlabInstrument)
    _create_discovery_subtree(basenode=connectors,baseclass=DlabConnector)
    _create_discovery_subtree(basenode=formatters,baseclass=Dlabformatter)
    
    for pre,_,nd in RenderTree(node=root):
        res += f"{pre}{nd.name}\n"
    
    return res
        