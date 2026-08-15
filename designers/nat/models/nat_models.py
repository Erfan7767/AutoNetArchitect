from dataclasses import dataclass,field
@dataclass
class NATRule:
    """NAT rule artifact."""
    kind:str
    source:str|None=None
    destination:str|None=None
    public_ip:str|None=None
    private_ip:str|None=None
    protocol:str|None=None
    port:int|None=None
    order:int=10
    metadata:dict=field(default_factory=dict)
