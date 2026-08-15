from dataclasses import dataclass,field
@dataclass
class CloudConnectivityModel:
    """Cloud connectivity design artifact."""
    provider:str
    method:str
    region:str|None=None
    account_id:str|None=None
    tunnels:int=0
    metadata:dict=field(default_factory=dict)
