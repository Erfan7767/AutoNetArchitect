"""Audit foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Audit(FoundationModel):
    """Validated audit contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
