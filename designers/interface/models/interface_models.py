from dataclasses import dataclass,field
@dataclass
class InterfaceRecord:
    """Vendor-specific interface inventory record."""
    name:str
    interface_type:str
    speed:str
    poe_capable:bool=False
    slot:int|None=None
    module:int|None=None
    port:int|None=None
    status:str="available"
    breakout_capable:bool=False
    metadata:dict=field(default_factory=dict)
