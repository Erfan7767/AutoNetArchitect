"""Config foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Config(FoundationModel):
    """Validated config contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
