"""Bom foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Bom(FoundationModel):
    """Validated bom contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
