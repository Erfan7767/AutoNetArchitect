"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class RedistributionModel:
    """Typed routing model."""
    source_protocol:str
    target_protocol:str
    metric:int|None=None
    tag:int|None=None
    route_map:str|None=None
