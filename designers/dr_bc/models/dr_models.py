from dataclasses import dataclass,field
@dataclass
class DRDesignModel:
    """Network DR design artifact."""
    strategy:str
    rpo:str|None=None
    rto:str|None=None
    metadata:dict=field(default_factory=dict)
