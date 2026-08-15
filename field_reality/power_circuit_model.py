"""Circuit, breaker, and feed redundancy data."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class PowerCircuitModel:
    """Circuit, breaker, and feed redundancy data."""
    circuit_id: str
    amperage: float | None = None
    voltage: float | None = None
    dedicated: bool | None = None
    feed_label: str | None = None
    redundant_pair_id: str | None = None
