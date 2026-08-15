"""Execution report construction."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ExecutionReport:
    """Summary of one phase execution."""
    phase_id: int
    status: str
    files: list[str]
    validation: dict[str, Any]
    issues: list[str]
    def to_dict(self) -> dict[str, Any]:
        """Serialize report."""
        return asdict(self)

class ExecutionReporter:
    """Create reports with consistent fields."""
    def create(self, phase_id: int, status: str, files: list[str], validation: dict[str, Any] | None = None, issues: list[str] | None = None) -> ExecutionReport:
        """Create a phase report."""
        return ExecutionReport(phase_id, status, files, validation or {}, issues or [])
