"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class ISISModel:
    """Typed routing model."""
    net:str|None=None
    levels:list[str]=field(default_factory=list)
    wide_metrics:bool=True
