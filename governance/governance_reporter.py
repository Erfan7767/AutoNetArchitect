"""Governance lifecycle reporting with explicit human checkpoints."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import Assumption, BaseDesigner, DecisionRecord

from .accountability_matrix import AccountabilityRequirement
from .emergency_change_policy import EmergencyAssessment
from .exception_waiver_model import WaiverAssessment
from .legal_boundary_notes import LegalBoundaryNote
from .signoff_policy import SignoffEvaluation


class LifecycleCheckpoint(BaseModel):
    """Human checkpoint summary for one workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    decision_class: str
    risk_class: str
    accountable_owner_role: str
    required_reviews: tuple[str, ...] = ()
    required_approvals: tuple[str, ...] = ()
    execution_authority_roles: tuple[str, ...] = ()
    status: str
    pending_checkpoints: tuple[str, ...] = ()
    escalation_path: tuple[str, ...] = ()


class GovernanceReport(BaseModel):
    """Machine-readable governance report artifact."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = "1.0"
    title_en: str = "Human Accountability and Sign-Off Governance Report"
    title_ar: str = "تقرير مساءلة الإنسان وحوكمة الاعتماد"
    lifecycle_checkpoints: tuple[LifecycleCheckpoint, ...] = ()
    pending_human_checkpoints: tuple[str, ...] = ()
    active_waivers: tuple[dict[str, Any], ...] = ()
    emergency_assessments: tuple[dict[str, Any], ...] = ()
    legal_boundary_notes: tuple[dict[str, Any], ...] = ()
    sot_basis: dict[str, str] = Field(default_factory=dict)
    decision_ids: tuple[str, ...] = ()
    assumption_keys: tuple[str, ...] = ()
    disclaimer_en: str = "This report records governance checkpoints and does not replace professional, legal, regulatory, or organizational accountability."
    disclaimer_ar: str = "يسجل هذا التقرير نقاط الحوكمة ولا يحل محل المسؤولية المهنية أو القانونية أو التنظيمية أو المؤسسية."


class GovernanceReporter(BaseDesigner):
    """Generate bilingual governance reports from policy evaluations."""

    def __init__(self) -> None:
        """Initialize reporter decision tracking."""
        super().__init__("GovernanceReporter")
        self.record_decision("governance_report_format", "checkpoint_and_boundary_explicit", "reports must expose pending human checkpoints rather than implying approval")

    def generate(self, *, project_id: str, requirements: Iterable[AccountabilityRequirement], evaluations: Iterable[SignoffEvaluation] = (), waivers: Iterable[WaiverAssessment] = (), emergencies: Iterable[EmergencyAssessment] = (), legal_notes: Iterable[LegalBoundaryNote] = (), sot_basis: dict[str, str] | None = None, report_id: str | None = None) -> GovernanceReport:
        """Create a report with one lifecycle checkpoint row per requirement."""
        evaluation_map = {item.workflow: item for item in evaluations}
        checkpoints: list[LifecycleCheckpoint] = []
        pending: list[str] = []
        decisions: list[str] = []
        assumptions: list[str] = []
        for requirement in requirements:
            evaluation = evaluation_map.get(requirement.workflow)
            status = evaluation.state if evaluation else "pending_evaluation"
            pending_items = evaluation.pending_checkpoints if evaluation else tuple(f"policy_evaluation:{requirement.workflow}",)
            checkpoints.append(LifecycleCheckpoint(workflow=requirement.workflow, decision_class=requirement.decision_class.value, risk_class=requirement.risk_class.value, accountable_owner_role=requirement.accountable_owner_role, required_reviews=tuple(role for role in requirement.required_reviewer_roles), required_approvals=tuple(role for role in requirement.required_approver_roles), execution_authority_roles=requirement.execution_authority_roles, status=status, pending_checkpoints=pending_items, escalation_path=requirement.escalation_path))
            pending.extend(f"{requirement.workflow}:{item}" for item in pending_items)
            decisions.append(f"matrix:{requirement.workflow}")
            if not evaluation:
                assumptions.append(f"evaluation_missing:{requirement.workflow}")
        waiver_dicts = tuple(item.model_dump(mode="json") for item in waivers if item.enforceable)
        emergency_dicts = tuple(item.model_dump(mode="json") for item in emergencies)
        legal_dicts = tuple(item.model_dump(mode="json") for item in legal_notes)
        report = GovernanceReport(report_id=report_id or f"GOV-{project_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", project_id=project_id, lifecycle_checkpoints=tuple(checkpoints), pending_human_checkpoints=tuple(dict.fromkeys(pending)), active_waivers=waiver_dicts, emergency_assessments=emergency_dicts, legal_boundary_notes=legal_dicts, sot_basis=sot_basis or {"status": "not supplied"}, decision_ids=tuple(decisions), assumption_keys=tuple(assumptions))
        self.record_decision(f"report:{report.report_id}", "generated", "governance report lists review, approval, accountability, and execution checkpoints")
        for assumption in assumptions:
            self.record_assumption(assumption, "missing", "no sign-off evaluation was supplied for this lifecycle checkpoint")
        return report

    def to_markdown(self, report: GovernanceReport) -> str:
        """Render a bilingual Markdown report without hiding pending checkpoints."""
        lines = [f"# {report.title_en} / {report.title_ar}", "", f"**Project:** {report.project_id}", f"**Generated:** {report.generated_at.isoformat()}", f"**Schema:** {report.schema_version}", "", "## Lifecycle Checkpoints / نقاط دورة الحياة", "", "| Workflow | Decision class | Risk | Accountable owner | Reviews | Approvals | Execution authority | Status | Pending |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
        for item in report.lifecycle_checkpoints:
            lines.append("| " + " | ".join([item.workflow, item.decision_class, item.risk_class, item.accountable_owner_role, ", ".join(item.required_reviews), ", ".join(item.required_approvals), ", ".join(item.execution_authority_roles), item.status, ", ".join(item.pending_checkpoints) or "none"]) + " |")
        pending_lines = [f"- {item}" for item in report.pending_human_checkpoints] or ["- none"]
        legal_lines = [f"- {item.get('subject', 'not supplied')}: {item.get('limitation', 'not supplied')}" for item in report.legal_boundary_notes] or ["- none"]
        lines.extend(["", "## Human Checkpoints / نقاط الاعتماد البشري", ""] + pending_lines + ["", "## Legal Boundary Notes / ملاحظات الحدود القانونية", ""] + legal_lines + ["", f"> {report.disclaimer_en}", f"> {report.disclaimer_ar}"])
        return "\n".join(lines) + "\n"

    def write_json(self, report: GovernanceReport, output_path: str | Path) -> Path:
        """Write a deterministic JSON governance artifact."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
