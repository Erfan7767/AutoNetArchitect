"""Cable pathway and separation constraints."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class PathwayModel:
    """Cable pathway and separation constraints."""
    pathway_id: str
    available_length_m: float | None = None
    fill_ratio: float | None = None
    separation_confirmed: bool = False
    fire_stopping_required: bool | None = None
