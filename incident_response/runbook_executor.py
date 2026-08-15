"""Human-driven incident runbook tracking without automatic command execution."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision
from .incident_models import IncidentCategory, IncidentRunbook, RunbookStep


class RunbookExecutor:
    """Load, display, and track incident runbooks; never execute command strings."""

    def __init__(self, runbook_dir: str | Path = "/home/ubuntu/AutoNetArchitect/data/incident_runbooks") -> None:
        """Initialize a local runbook repository."""
        self.runbook_dir = Path(runbook_dir)
        self._runbooks: dict[str, IncidentRunbook] = {}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def load(self, runbook_id: str, category: IncidentCategory) -> IncidentRunbook:
        """Load and validate one JSON runbook."""
        path = self.runbook_dir / f"{runbook_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"runbook not found: {runbook_id}")
        raw = json.loads(path.read_text(encoding="utf-8"))
        runbook = IncidentRunbook.model_validate({"runbook_id": str(raw.get("runbook_id", runbook_id)), "incident_category": raw.get("incident_category", category.value), "title": str(raw.get("title", runbook_id)), "version": str(raw.get("version", "1.0")), "steps": raw.get("steps", []), "requires_incident_commander": bool(raw.get("requires_incident_commander", True)), "evidence_preservation_notes": raw.get("evidence_preservation_notes", [])})
        self._runbooks[runbook.runbook_id] = runbook
        self.decisions.append(make_decision("RunbookExecutor", f"runbook:{runbook.runbook_id}:load", "validated_local_runbook", "load only a local JSON runbook that passes the Pydantic contract", ["validated_local_runbook", "remote_unvalidated_runbook"], {"validated_local_runbook": "selected", "remote_unvalidated_runbook": "rejected"}))
        return runbook.model_copy(deep=True)

    def get(self, runbook_id: str) -> IncidentRunbook:
        """Return a loaded runbook."""
        if runbook_id not in self._runbooks:
            raise KeyError(f"runbook not loaded: {runbook_id}")
        return self._runbooks[runbook_id].model_copy(deep=True)

    def start(self, runbook_id: str, *, incident_commander: str) -> IncidentRunbook:
        """Start a runbook only with a human commander."""
        runbook = self.get(runbook_id)
        if runbook.requires_incident_commander and not incident_commander:
            raise ValueError("incident commander is required by the runbook")
        return runbook

    def record_step(self, runbook_id: str, step_id: str, *, executed_by: str, status: str, result: str, deviation: str = "") -> IncidentRunbook:
        """Record a human-reported step result and branch metadata."""
        if status not in {"completed", "failed", "skipped", "not_started"}:
            raise ValueError("unsupported runbook step status")
        runbook = self._runbooks.get(runbook_id)
        if runbook is None:
            raise KeyError(f"runbook not loaded: {runbook_id}")
        if not executed_by or not result:
            raise ValueError("executed_by and result are required")
        steps = list(runbook.steps)
        index = next((position for position, step in enumerate(steps) if step.step_id == step_id), None)
        if index is None:
            raise KeyError(f"unknown runbook step: {step_id}")
        steps[index] = steps[index].model_copy(update={"status": status, "result": result, "executed_by": executed_by, "executed_at": datetime.now(timezone.utc)})
        updated = runbook.model_copy(update={"steps": steps}, deep=True)
        self._runbooks[runbook_id] = updated
        if deviation:
            self.assumptions.append(make_assumption(f"runbook:{runbook_id}:{step_id}:deviation", deviation, "runbook deviation is recorded for review and not silently normalized", True))
        self.decisions.append(make_decision("RunbookExecutor", f"runbook:{runbook_id}:{step_id}:record", status, "record a human-reported outcome without executing the command field", ["completed", "failed", "skipped"], {item: "not selected by supplied result" for item in ["completed", "failed", "skipped"] if item != status}))
        return updated.model_copy(deep=True)
