from dataclasses import dataclass,field
@dataclass
class AccessPortModel:
    """Layer-2 model."""
    interface:str
    role:str
    data_vlan:int|None=None
    voice_vlan:int|None=None
