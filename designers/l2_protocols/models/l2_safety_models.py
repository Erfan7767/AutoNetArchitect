from dataclasses import dataclass,field
@dataclass
class L2SafetyModel:
    """Layer-2 model."""
    features:list[str]=field(default_factory=list)
    coverage:dict=field(default_factory=dict)
