"""Lifecycle metadata for formulas and planning rules."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass
class FormulaVersion:
    """Versioned formula with source and deprecation metadata."""
    name: str
    version: str
    source: str
    expression: str
    status: str = "active"
    deprecated_reason: str | None = None
class FormulaLifecycle:
    """Register, deprecate, and retrieve active formula versions."""
    def __init__(self) -> None: self.formulas: dict[tuple[str, str], FormulaVersion] = {}
    def register(self, formula: FormulaVersion) -> FormulaVersion:
        """Register a formula version."""
        if not formula.source or not formula.expression: raise ValueError("formula source and expression are required")
        self.formulas[(formula.name, formula.version)] = formula; return formula
    def deprecate(self, name: str, version: str, reason: str) -> FormulaVersion:
        """Deprecate a formula version."""
        formula = self.formulas[(name, version)]; formula.status = "deprecated"; formula.deprecated_reason = reason; return formula
    def active(self, name: str) -> list[FormulaVersion]:
        """Return active versions for a formula name."""
        return [formula for (formula_name, _), formula in self.formulas.items() if formula_name == name and formula.status == "active"]
