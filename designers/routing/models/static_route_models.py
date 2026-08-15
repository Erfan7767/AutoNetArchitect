"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class StaticRouteModel:
    """Typed routing model."""
    prefix:str
    next_hop:str|None=None
    exit_interface:str|None=None
    administrative_distance:int=1
