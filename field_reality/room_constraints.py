"""Room dimensions, fire rating, and environmental restrictions."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class RoomConstraints:
    """Room dimensions, fire rating, and environmental restrictions."""
    room_id: str
    floor_area_m2: float | None = None
    ceiling_height_m: float | None = None
    fire_rating_confirmed: bool | None = None
    environmental_restrictions: list[str] = field(default_factory=list)
