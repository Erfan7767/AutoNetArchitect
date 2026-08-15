from dataclasses import dataclass,field
@dataclass
class ProfilingModel:
    """NAC model."""
    methods:list[str]=field(default_factory=list)
    server:str|None=None
