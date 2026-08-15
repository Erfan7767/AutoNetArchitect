"""Routing model contract."""
from __future__ import annotations
from dataclasses import dataclass,field
@dataclass
class BFDModel:
    """Typed routing model."""
    min_tx_ms:int
    min_rx_ms:int
    multiplier:int
    platform_evidence_ids:list[str]=field(default_factory=list)
