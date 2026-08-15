"""Reporting for mandatory checkpoints and formal no-go results."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .mandatory_checkpoints import CheckpointRecord, MandatoryCheckpointDefinition, MandatoryCheckpointRegistry
from .no_go_policy import NoGoBlocker, NoGoEvaluation


class CheckpointReport(BaseModel):
    """Machine-readable mandatory checkpoint report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    checkpoints: tuple[dict, ...] = ()
    unresolved_checkpoint_ids: tuple[str, ...] = ()
    blockers: tuple[dict, ...] = ()
    no_go_evaluations: tuple[dict, ...] = ()
    release_blocked: bool = True
    sot_basis: dict[str, str] = Field(default_factory=dict)


class CheckpointReporter(BaseDesigner):
    """Generate bilingual checkpoint and no-go reports."""

    def __init__(self, *, registry: MandatoryCheckpointRegistry | None = None) -> None:
        """Initialize reporter."""
        super().__init__("CheckpointReporter")
        self.registry = registry or MandatoryCheckpointRegistry()
        self.record_decision("checkpoint_reporting_policy", "formal_status_explicit", "reports expose unresolved checkpoints and blockers as release controls")

    def generate(self, *, project_id: str, records: Iterable[CheckpointRecord] = (), evaluations: Iterable[NoGoEvaluation] = (), blockers: Iterable[NoGoBlocker] = (), sot_basis: dict[str, str] | None = None, report_id: str | None = None) -> CheckpointReport:
        """Generate a report with registry definitions and actual record status."""
        record_map = {record.checkpoint_id: record for record in records}
        rows: list[dict] = []
        unresolved: list[str] = []
        for definition in self.registry.all():
            record = record_map.get(definition.checkpoint_id)
            ready = bool(record and record.is_release_ready(definition))
            row = {"checkpoint_id": definition.checkpoint_id, "workflow_stage": definition.workflow_stage, "control_type": definition.control_type.value, "required_human_role": definition.required_human_role, "status": record.status.value if record else "pending", "reviewer_id": record.reviewer_id if record else "", "decision_reference": record.decision_reference if record else "", "evidence_ids": list(record.evidence_ids) if record else [], "release_ready": ready}
            rows.append(row)
            if not ready:
                unresolved.append(definition.checkpoint_id)
        blocker_items = tuple(item.model_dump(mode="json") for item in blockers)
        evaluation_items = tuple(item.model_dump(mode="json") for item in evaluations)
        report = CheckpointReport(report_id=report_id or f"CHK-{project_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", project_id=project_id, checkpoints=tuple(rows), unresolved_checkpoint_ids=tuple(unresolved), blockers=blocker_items, no_go_evaluations=evaluation_items, release_blocked=bool(unresolved) or any(not item.resolved for item in blockers) or any(item.outcome.value == "no_go" for item in evaluations), sot_basis=sot_basis or {"status": "not supplied"})
        self.record_decision(f"checkpoint_report:{report.report_id}", "blocked" if report.release_blocked else "clear", "report preserves formal checkpoint status and no-go outcome")
        return report

    def to_markdown(self, report: CheckpointReport) -> str:
        """Render a bilingual Markdown checkpoint report."""
        lines = [f"# Mandatory Checkpoint Report / تقرير نقاط المراجعة الإلزامية", "", f"**Project / المشروع:** {report.project_id}", f"**Generated / التوليد:** {report.generated_at.isoformat()}", f"**Release blocked / الإصدار محظور:** {report.release_blocked}", "", "| Checkpoint | Stage | Control | Role | Status | Release ready |", "| --- | --- | --- | --- | --- | --- |"]
        for item in report.checkpoints:
            lines.append("| " + " | ".join([item["checkpoint_id"], item["workflow_stage"], item["control_type"], item["required_human_role"], item["status"], str(item["release_ready"])]) + " |")
        lines.extend(["", "## Unresolved Checkpoints / النقاط غير المحلولة", ""])
        lines.extend(f"- `{item}`" for item in report.unresolved_checkpoint_ids) or lines.append("- none / لا يوجد")
        lines.extend(["", "## Blockers / العوائق", ""])
        if report.blockers:
            lines.extend(f"- `{item.get('blocker_id', 'unknown')}` — {item.get('blocking_reason', 'not supplied')} — resolution: {item.get('required_resolution', 'not supplied')}" for item in report.blockers)
        else:
            lines.append("- none / لا يوجد")
        return "\n".join(lines) + "\n"

    def write_json(self, report: CheckpointReport, output_path: str | Path) -> Path:
        """Write checkpoint report JSON."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
