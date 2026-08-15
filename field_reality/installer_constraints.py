"""Installer capability and access restrictions."""
from __future__ import annotations
from dataclasses import dataclass, field
@dataclass
class InstallerConstraints:
    """Installer capability and access restrictions."""
    installer_id: str
    certified_vendors: list[str] = field(default_factory=list)
    maximum_shift_hours: float | None = None
    prohibited_methods: list[str] = field(default_factory=list)
    required_supervision: list[str] = field(default_factory=list)
