"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class EIGRPModel:
    """Typed routing model."""
    asn:int|None=None
    named_mode:bool=True
    networks:list[str]=field(default_factory=list)
