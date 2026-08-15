"""SourceOfTruth foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class SourceOfTruth(FoundationModel):
    """Validated source of truth contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
