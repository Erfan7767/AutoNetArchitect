from dataclasses import dataclass,field
@dataclass
class RadiusModel:
    """NAC model."""
    server_type:str|None=None
    servers:list[str]=field(default_factory=list)
    auth_port:int=1812
    acct_port:int=1813
