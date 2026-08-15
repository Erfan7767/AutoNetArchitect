from dataclasses import dataclass,field
@dataclass
class MPLSCircuit:
    """MPLS circuit contract model."""
    site:str
    circuit_id:str|None=None
    bandwidth_mbps:int|None=None
    pe_ip:str|None=None
    ce_ip:str|None=None
    metadata:dict=field(default_factory=dict)
