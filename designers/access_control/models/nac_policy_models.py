from dataclasses import dataclass,field
@dataclass
class NACPolicyModel:
    """NAC model."""
    identity_type:str
    vlan:int|None=None
    acl:str|None=None
    sgt:str|None=None
