"""Human-supplied assumptions registry."""
from __future__ import annotations
from typing import Any
from pydantic import Field
from .base import FoundationModel
class Assumption(FoundationModel):
    """One explicit assumption or human-supplied mandatory fact."""
    key: str
    value: Any = None
    source: str = "human"
    mandatory: bool = True
    confirmed: bool = False
class AssumptionRegistry(FoundationModel):
    """Collection enforcing explicit assumption tracking."""
    items: list[Assumption] = Field(default_factory=list)
    def add(self, assumption: Assumption) -> None:
        """Add an assumption, replacing the same key."""
        self.items = [item for item in self.items if item.key != assumption.key] + [assumption]
    def unresolved(self) -> list[Assumption]:
        """Return mandatory assumptions that remain unconfirmed."""
        return [item for item in self.items if item.mandatory and not item.confirmed]
