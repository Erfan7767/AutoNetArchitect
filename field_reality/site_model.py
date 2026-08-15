"""Site reality model with explicit unknowns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
@dataclass
class SiteModel:
    """Represent measured or explicitly unresolved site constraints."""
    site_id: str
    site_type: str
    building_constraints: dict[str, Any] = field(default_factory=dict)
    room_data_completeness: float = 0.0
    available_rack_units: int | None = None
    available_power_feeds: int | None = None
    ups_present: bool | None = None
    hvac_confidence: float = 0.0
    access_restrictions: list[str] = field(default_factory=list)
    maintenance_windows: list[str] = field(default_factory=list)
    installer_limitations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    human_supplied_mandatory: list[str] = field(default_factory=list)
    def missing_fields(self) -> list[str]:
        """Return physical fields unavailable for a responsible assessment."""
        missing = []
        for name, value in (("available_rack_units", self.available_rack_units), ("available_power_feeds", self.available_power_feeds), ("ups_present", self.ups_present)):
            if value is None: missing.append(name)
        if self.room_data_completeness < 1.0: missing.append("room_data_completeness")
        if self.hvac_confidence < 0.8: missing.append("hvac_confidence")
        return missing
    def validate(self) -> None:
        """Validate confidence and non-negative measured values."""
        if not 0 <= self.room_data_completeness <= 1 or not 0 <= self.hvac_confidence <= 1: raise ValueError("completeness and confidence must be between zero and one")
        if self.available_rack_units is not None and self.available_rack_units < 0: raise ValueError("rack units cannot be negative")
