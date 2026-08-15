"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class RoutingPolicyModel:
    """Typed routing model."""
    name:str
    sequence:int
    action:str
    match:dict=field(default_factory=dict)
    set_actions:dict=field(default_factory=dict)
