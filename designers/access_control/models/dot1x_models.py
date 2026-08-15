from dataclasses import dataclass,field
@dataclass
class Dot1XModel:
    """NAC model."""
    mode:str
    host_mode:str="single-host"
    auth_order:list[str]=field(default_factory=lambda:["dot1x","mab"])
