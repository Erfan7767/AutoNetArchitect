"""Versioned formula registry with provenance and confidence."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
@dataclass(frozen=True)
class Formula:
    """A named formula with source, version, and confidence."""
    name: str
    calculate: Callable[..., float]
    source: str
    version: str
    confidence: float
class FormulaRegistry:
    """Register and evaluate auditable formulas."""
    def __init__(self) -> None:
        self._formulas: dict[str, Formula] = {"user_capacity": Formula("user_capacity", lambda users, growth=0.2: users * (1 + growth), "internal planning baseline", "1.0", 0.75), "usable_ipv4_hosts": Formula("usable_ipv4_hosts", lambda prefix: max(0, 2 ** (32 - prefix) - 2), "RFC 1918 planning convention", "1.0", 0.9)}
    def register(self, formula: Formula) -> None:
        """Register or replace a formula."""
        if not 0 <= formula.confidence <= 1: raise ValueError("confidence must be between zero and one")
        self._formulas[formula.name] = formula
    def evaluate(self, name: str, **kwargs: float) -> dict[str, object]:
        """Evaluate a formula and return result with provenance."""
        formula = self._formulas[name]; return {"value": formula.calculate(**kwargs), "source": formula.source, "version": formula.version, "confidence": formula.confidence}
