"""Common Pydantic model behavior."""
from __future__ import annotations
from typing import Any, Self
from pydantic import BaseModel, ConfigDict, Field
from ..constants import SCHEMA_VERSION
class FoundationModel(BaseModel):
    """Base model with schema version and dictionary conversion."""
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    schema_version: str = Field(default=SCHEMA_VERSION, frozen=True)
    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dictionary."""
        return self.model_dump(mode="json")
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Construct a validated model from a dictionary."""
        return cls.model_validate(data)
