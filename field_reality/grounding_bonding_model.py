"""Grounding and bonding verification."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class GroundingBondingModel:
    """Grounding and bonding verification."""
    room_id: str
    grounding_present: bool | None = None
    bonding_verified: bool | None = None
    test_record_id: str | None = None
