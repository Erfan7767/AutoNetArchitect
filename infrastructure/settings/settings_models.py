"""Pydantic settings contracts."""
from pydantic import BaseModel, Field
class Settings(BaseModel):
    """Validated application settings."""
    environment: str = 'development'
    values: dict[str, object] = Field(default_factory=dict)
