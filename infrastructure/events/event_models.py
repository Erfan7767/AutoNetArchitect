"""Serializable event models."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
class Event(BaseModel):
    """Immutable-enough event envelope."""
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    event_id: str = ''
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = 'system'
