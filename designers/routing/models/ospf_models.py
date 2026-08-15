"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class OSPFModel:
    """Typed routing model."""
    process_id:int|None=None
    router_id:str|None=None
    reference_bandwidth_mbps:int|None=None
    areas:list[dict]=field(default_factory=list)
