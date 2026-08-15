from dataclasses import dataclass,field
@dataclass
class FHRPGroup:
    """FHRP group artifact."""
    vlan_id:int
    protocol:str
    virtual_ip:str
    priority:int=100
    preempt:bool=True
    tracking:list[dict]=field(default_factory=list)
