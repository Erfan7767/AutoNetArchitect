"""MDF or IDF rack space capacity."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class RackSpaceModel:
    """MDF or IDF rack space capacity."""
    room_id: str
    rack_units_total: int | None = None
    rack_units_used: int | None = None
    weight_capacity_kg: float | None = None
    mdf_or_idf: str = "unknown"
