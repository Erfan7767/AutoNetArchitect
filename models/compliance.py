"""Compliance foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Compliance(FoundationModel):
    """Validated compliance contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
