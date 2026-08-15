"""Architecture decision records."""
from __future__ import annotations
from pydantic import Field
from .base import FoundationModel
class DecisionRecord(FoundationModel):
    """Record context, decision, alternatives, and consequences."""
    decision_id: str
    title: str
    context: str
    decision: str
    alternatives: list[str] = Field(default_factory=list)
    consequences: list[str] = Field(default_factory=list)
    status: str = "accepted"
