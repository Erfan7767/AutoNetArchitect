"""Reporting for engineer-supervised workflow runs."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .supervision_context import SupervisionContext, SupervisionEvent
from .workflow_mode import SupervisionDecision


class SupervisedReport(BaseModel):
    """Machine-readable supervised workflow report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    workflow_run_id: str
    mode: str
    high_assurance: bool
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_checkpoints: int = 0
    human_intervention_count: int = 0
    blocked_count: int = 0
    auto_continue_count: int = 0
    requires_review_count: int = 0
    requires_approval_count: int = 0
    human_interventions: tuple[dict[str, Any], ...] = ()
    pending_checkpoints: tuple[dict[str, Any], ...] = ()
    blocked_checkpoints: tuple[dict[str, Any], ...] = ()
    stage_summary: dict[str, dict[str, int]] = Field(default_factory=dict)
    sot_basis: dict[str, str] = Field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()
    disclaimer_en: str = "This report records supervised workflow events; it does not transfer professional accountability from the human engineer."
    disclaimer_ar: str = "يسجل هذا التقرير أحداث سير العمل تحت الإشراف ولا ينقل المسؤولية المهنية من المهندس البشري."


class SupervisedReporter(BaseDesigner):
    """Generate and serialize supervised-mode run reports."""

    def __init__(self) -> None:
        """Initialize reporter decision tracking."""
        super().__init__("SupervisedReporter")
        self.record_decision("reporting_policy", "human_interventions_explicit", "reports must surface all review, approval, and block events")

    def generate(self, context: SupervisionContext, *, report_id: str | None = None) -> SupervisedReport:
        """Generate a report from all retained context events."""
        events = tuple(context.events)
        interventions = tuple(self._event_dict(item) for item in events if item.decision in {SupervisionDecision.REQUIRES_REVIEW, SupervisionDecision.REQUIRES_APPROVAL, SupervisionDecision.BLOCKED} or item.actor_id != "system")
        pending = tuple(self._event_dict(item) for item in context.pending_events())
        blocked = tuple(self._event_dict(item) for item in events if item.decision == SupervisionDecision.BLOCKED)
        summary: dict[str, dict[str, int]] = {}
        for event in events:
            stage = event.workflow_stage.value
            counts = summary.setdefault(stage, {decision.value: 0 for decision in SupervisionDecision})
            counts[event.decision.value] += 1
        report = SupervisedReport(report_id=report_id or f"SUP-{context.workflow_run_id}", project_id=context.project_id, workflow_run_id=context.workflow_run_id, mode=context.mode.value, high_assurance=context.high_assurance, total_checkpoints=len(events), human_intervention_count=len(interventions), blocked_count=sum(1 for item in events if item.decision == SupervisionDecision.BLOCKED), auto_continue_count=sum(1 for item in events if item.decision == SupervisionDecision.AUTO_CONTINUE), requires_review_count=sum(1 for item in events if item.decision == SupervisionDecision.REQUIRES_REVIEW), requires_approval_count=sum(1 for item in events if item.decision == SupervisionDecision.REQUIRES_APPROVAL), human_interventions=interventions, pending_checkpoints=pending, blocked_checkpoints=blocked, stage_summary=summary, sot_basis=context.sot_basis, evidence_ids=context.evidence_ids)
        self.record_decision(f"report:{report.report_id}", "generated", "report includes every supervised checkpoint requiring human interaction")
        return report

    def to_markdown(self, report: SupervisedReport) -> str:
        """Render a bilingual Markdown summary."""
        lines = [f"# Engineer-Supervised Workflow Report / تقرير سير العمل تحت إشراف المهندس", "", f"**Project / المشروع:** {report.project_id}", f"**Workflow run / تشغيل سير العمل:** {report.workflow_run_id}", f"**Mode / النمط:** {report.mode}", f"**Generated / تاريخ التوليد:** {report.generated_at.isoformat()}", "", "## Counts / الإحصاءات", "", "| Metric | Count |", "| --- | ---: |", f"| Total checkpoints / إجمالي النقاط | {report.total_checkpoints} |", f"| Human interventions / تدخلات بشرية | {report.human_intervention_count} |", f"| Auto-continue / استمرار تلقائي محدود | {report.auto_continue_count} |", f"| Requires review / يتطلب مراجعة | {report.requires_review_count} |", f"| Requires approval / يتطلب اعتماداً | {report.requires_approval_count} |", f"| Blocked / محظور | {report.blocked_count} |", "", "## Human Intervention Summary / ملخص التدخل البشري", ""]
        if report.human_interventions:
            for item in report.human_interventions:
                lines.append(f"- `{item['checkpoint_id']}` — {item['decision']} — actor `{item['actor_id']}` — {item['action'] or 'pending human action'}")
        else:
            lines.append("- none recorded / لا توجد تدخلات مسجلة")
        lines.extend(["", "## Pending and Blocked / المعلّق والمحظور", ""])
        if report.pending_checkpoints or report.blocked_checkpoints:
            for item in report.pending_checkpoints + report.blocked_checkpoints:
                lines.append(f"- `{item['checkpoint_id']}` — {item['decision']} — {item['rationale'] or 'human action required'}")
        else:
            lines.append("- none / لا يوجد")
        lines.extend(["", f"> {report.disclaimer_en}", f"> {report.disclaimer_ar}"])
        return "\n".join(lines) + "\n"

    def write_json(self, report: SupervisedReport, output_path: str | Path) -> Path:
        """Write a JSON report artifact."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target

    @staticmethod
    def _event_dict(event: SupervisionEvent) -> dict[str, Any]:
        """Serialize an event without raw secret values."""
        return {"event_id": event.event_id, "checkpoint_id": event.checkpoint_id, "workflow_stage": event.workflow_stage.value, "decision": event.decision.value, "actor_id": event.actor_id, "actor_role": event.actor_role, "action": event.action, "rationale": event.rationale, "reference": event.reference, "evidence_ids": list(event.evidence_ids), "created_at": event.created_at.isoformat()}
