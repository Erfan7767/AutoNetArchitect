"""Wan foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Wan(FoundationModel):
    """Validated wan contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
