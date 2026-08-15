from dataclasses import dataclass,field
@dataclass
class STPModel:
    """Layer-2 model."""
    mode:str
    roots:dict=field(default_factory=dict)
