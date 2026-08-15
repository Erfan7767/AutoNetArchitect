"""Access and maintenance window constraints."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class AccessWindowModel:
    """Access and maintenance window constraints."""
    site_id: str
    windows: list[str] = field(default_factory=list)
    escort_required: bool | None = None
    permit_required: bool | None = None
    lead_time_days: int | None = None
