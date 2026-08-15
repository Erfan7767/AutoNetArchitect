"""Deployment foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Deployment(FoundationModel):
    """Validated deployment contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
