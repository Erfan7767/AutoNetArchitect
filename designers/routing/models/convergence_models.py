"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class ConvergenceModel:
    """Typed routing model."""
    scenario:str
    estimated_ms:float
    evidence_basis:str
