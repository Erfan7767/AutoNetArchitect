"""Typed models for pre-execution contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .constants import SCHEMA_VERSION
from .exceptions import ValidationError
@dataclass(frozen=True)
class HumanSuppliedMandatory:
    """A fact that must be supplied or confirmed by a human."""
    field_name: str
    value: str | None = None
    required: bool = True
    source: str = 'human'
    def validate(self) -> None:
        """Reject malformed mandatory fields."""
        if not self.field_name or self.source != 'human': raise ValidationError('invalid human-supplied field')
@dataclass(frozen=True)
class VendorProfile:
    """Supported vendor contract."""
    name: str
    supported: bool = False
    schema_version: str = SCHEMA_VERSION
    def validate(self) -> None:
        """Validate vendor support and schema version."""
        if self.name != 'Huawei' or not self.supported: raise ValidationError('vendor is not supported in V1')
@dataclass(frozen=True)
class ProjectState:
    """Project state contract."""
    state: str
    schema_version: str = SCHEMA_VERSION
    def validate(self) -> None:
        """Validate the state name."""
        if self.state not in {'draft','specified','designed','validated','approved','deployed','blocked'}: raise ValidationError('invalid project state')
