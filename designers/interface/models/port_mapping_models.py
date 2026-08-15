from dataclasses import dataclass
@dataclass
class PortMapping:
    """Final port mapping row."""
    interface_name:str
    role:str
    vlan:int|None=None
    speed:str|None=None
    duplex:str="auto"
    poe:bool=False
    description:str=""
    remote_device:str|None=None
    remote_interface:str|None=None
    cable_id:str|None=None
    status:str="allocated"
