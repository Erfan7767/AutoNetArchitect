"""Reporting for engineer review-console sessions."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .decision_workbench import DecisionWorkbenchView
from .override_panel import OverrideView
from .review_session import ReviewSession
from .signoff_panel import SignoffPanelView


class ReviewConsoleReport(BaseModel):
    """Machine-readable console report for a human review session."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    session_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision: dict[str, Any]
    alternatives: tuple[dict[str, Any], ...] = ()
    evidence: tuple[dict[str, Any], ...] = ()
    risks: tuple[dict[str, Any], ...] = ()
    unresolved_items: tuple[dict[str, Any], ...] = ()
    overrides: tuple[dict[str, Any], ...] = ()
    signoff: dict[str, Any] = Field(default_factory=dict)
    session: dict[str, Any] = Field(default_factory=dict)
    human_action_required: bool = True
    production_claim_allowed: bool = False
    source_references: dict[str, str] = Field(default_factory=dict)


class ReviewConsoleReporter(BaseDesigner):
    """Generate a review artifact without making a business decision."""

    def __init__(self) -> None:
        """Initialize console reporter."""
        super().__init__("ReviewConsoleReporter")
        self.record_decision("console_report_policy", "review_surface_only", "report consolidates source views for an engineer and never changes approval or decision state")

    def generate(self, *, workbench: DecisionWorkbenchView, session: ReviewSession, overrides: Iterable[OverrideView] = (), signoff: SignoffPanelView | None = None, report_id: str | None = None) -> ReviewConsoleReport:
        """Generate a report from already-built presentation views."""
        override_items = tuple(item.model_dump(mode="json") for item in overrides)
        signoff_data = signoff.model_dump(mode="json") if signoff is not None else {}
        human_action = bool(workbench.unresolved_items or workbench.required_approvals or any(not item.resolved for item in workbench.risks) or not signoff_data.get("allowed", False))
        report = ReviewConsoleReport(report_id=report_id or f"RC-{session.session_id}", project_id=session.project_id, session_id=session.session_id, decision=workbench.model_dump(mode="json"), alternatives=tuple(item.model_dump(mode="json") for item in workbench.alternatives), evidence=tuple(item.model_dump(mode="json") for item in workbench.evidence_chain), risks=tuple(item.model_dump(mode="json") for item in workbench.risks), unresolved_items=tuple(item.model_dump(mode="json") for item in workbench.unresolved_items), overrides=override_items, signoff=signoff_data, session=session.model_dump(mode="json"), human_action_required=human_action, production_claim_allowed=workbench.production_claim_allowed, source_references=workbench.source_references)
        self.record_decision(f"console_report:{report.report_id}", "generated", "console report presents all source views and human checkpoints")
        return report

    def to_markdown(self, report: ReviewConsoleReport) -> str:
        """Render a bilingual engineer review report."""
        decision = report.decision
        lines = [f"# Engineer Review Console Report / تقرير مساحة مراجعة المهندس", "", f"**Project / المشروع:** {report.project_id}", f"**Session / الجلسة:** {report.session_id}", f"**Generated / التوليد:** {report.generated_at.isoformat()}", f"**Recommendation / التوصية:** {decision.get('chosen_recommendation')}", f"**Confidence / الثقة:** {decision.get('confidence')}", f"**Human action required / يلزم تدخل بشري:** {report.human_action_required}", "", "## Rationale / المبرر", "", str(decision.get("rationale", "")), "", "## Alternatives / البدائل", "", "| Alternative | Score | Selected | Rejection reasons |", "| --- | ---: | --- | --- |"]
        for item in report.alternatives:
            lines.append(f"| {item.get('name')} | {item.get('score')} | {item.get('selected')} | {'; '.join(item.get('rejection_reasons', []))} |")
        lines.extend(["", "## Evidence / الأدلة", ""])
        for item in report.evidence:
            lines.append(f"- `{item.get('evidence_id')}` — {item.get('source_type')} — {item.get('status')} — {item.get('trace_reference')}")
        if not report.evidence:
            lines.append("- none loaded / لم يتم تحميل أدلة")
        lines.extend(["", "## Risks and Unresolved Items / المخاطر والعناصر غير المحلولة", ""])
        for item in report.risks + report.unresolved_items:
            lines.append(f"- `{item.get('risk_id', item.get('item_id'))}` — {item.get('description')} — action: {item.get('mitigation', item.get('required_action', 'review required'))}")
        if not report.risks and not report.unresolved_items:
            lines.append("- none recorded / لا توجد عناصر مسجلة")
        lines.extend(["", "## Sign-off / الاعتماد", "", f"- state: {report.signoff.get('state', 'not supplied')}", f"- pending checkpoints: {', '.join(report.signoff.get('pending_checkpoints', [])) or 'none'}", "", "> This console is a review surface. It does not transfer accountability or execute approvals.", "> هذه المساحة واجهة مراجعة ولا تنقل المسؤولية ولا تنفذ الاعتمادات."])
        return "\n".join(lines) + "\n"

    def write_json(self, report: ReviewConsoleReport, output_path: str | Path) -> Path:
        """Write report JSON."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
