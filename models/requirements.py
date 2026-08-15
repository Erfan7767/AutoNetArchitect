"""Requirements foundation model."""
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Requirements(FoundationModel):
    """Validated requirements contract."""
    name: str = ""
    description: str = ""
    attributes: dict[str, Any] = Field(default_factory=dict)
