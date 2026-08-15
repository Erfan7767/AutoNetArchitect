"""HVAC and thermal capacity confidence."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class CoolingModel:
    """HVAC and thermal capacity confidence."""
    room_id: str
    hvac_type: str | None = None
    capacity_kw: float | None = None
    measured_temperature_c: float | None = None
    confidence: float = 0.0
