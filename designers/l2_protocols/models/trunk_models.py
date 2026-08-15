from dataclasses import dataclass,field
@dataclass
class TrunkModel:
    """Layer-2 model."""
    interface:str
    allowed_vlans:list[int]=field(default_factory=list)
    native_vlan:int=999
