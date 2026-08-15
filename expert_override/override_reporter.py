"""Reporting for expert overrides and engineering interventions."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .override_models import DecisionOrigin, OverrideApplication


class OverrideReport(BaseModel):
    """Machine-readable override provenance report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_overrides: int
    machine_made_decisions: tuple[dict, ...] = ()
    human_overridden_decisions: tuple[dict, ...] = ()
    human_originated_decisions: tuple[dict, ...] = ()
    rejected_interventions: tuple[dict, ...] = ()
    revalidation_pending: tuple[dict, ...] = ()
    revalidation_blocked: tuple[dict, ...] = ()
    disclaimer_en: str = "An override records human intervention; it does not prove that the resulting engineering decision is correct or production-safe."
    disclaimer_ar: str = "يسجل الـ override تدخلاً بشرياً ولا يثبت أن القرار الهندسي الناتج صحيح أو آمن للإنتاج."


class OverrideReporter(BaseDesigner):
    """Generate bilingual, provenance-preserving override reports."""

    def __init__(self) -> None:
        """Initialize reporter decision tracking."""
        super().__init__("OverrideReporter")
        self.record_decision("override_report_policy", "origin_and_revalidation_explicit", "reports distinguish machine, human-overridden, and human-originated decisions")

    def generate(self, *, project_id: str, applications: Iterable[OverrideApplication], report_id: str | None = None) -> OverrideReport:
        """Generate a report without collapsing decision origins."""
        items = tuple(applications)
        machine: list[dict] = []
        overridden: list[dict] = []
        originated: list[dict] = []
        rejected: list[dict] = []
        pending: list[dict] = []
        blocked: list[dict] = []
        for application in items:
            item = application.model_dump(mode="json")
            if application.status != "applied":
                rejected.append(item)
            elif application.origin == DecisionOrigin.HUMAN_OVERRIDDEN:
                overridden.append(item)
            elif application.origin == DecisionOrigin.HUMAN_ORIGINATED:
                originated.append(item)
            if application.revalidation_status.value in {"required", "scheduled"}:
                pending.append(item)
            if application.revalidation_status.value == "blocked":
                blocked.append(item)
        report = OverrideReport(report_id=report_id or f"OVR-{project_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", project_id=project_id, total_overrides=len(items), machine_made_decisions=tuple(machine), human_overridden_decisions=tuple(overridden), human_originated_decisions=tuple(originated), rejected_interventions=tuple(rejected), revalidation_pending=tuple(pending), revalidation_blocked=tuple(blocked))
        self.record_decision(f"report:{report.report_id}", "generated", "override report preserves intervention origin and downstream revalidation state")
        return report

    def to_markdown(self, report: OverrideReport) -> str:
        """Render a bilingual Markdown override report."""
        lines = [f"# Expert Override Report / تقرير التدخل الهندسي", "", f"**Project / المشروع:** {report.project_id}", f"**Generated / تاريخ التوليد:** {report.generated_at.isoformat()}", f"**Total / الإجمالي:** {report.total_overrides}", "", "| Origin / المصدر | Count / العدد |", "| --- | ---: |", f"| Machine-made / قرار آلي | {len(report.machine_made_decisions)} |", f"| Human-overridden / قرار آلي عُدّل بشرياً | {len(report.human_overridden_decisions)} |", f"| Human-originated / قرار بشري أصلي | {len(report.human_originated_decisions)} |", f"| Rejected / مرفوض | {len(report.rejected_interventions)} |", "", "## Revalidation / إعادة التحقق", ""]
        for item in report.revalidation_pending:
            lines.append(f"- `{item['override_id']}` — scheduled/required for downstream artifacts")
        if not report.revalidation_pending:
            lines.append("- none / لا يوجد")
        lines.extend(["", "## Rejected Interventions / التدخلات المرفوضة", ""])
        for item in report.rejected_interventions:
            lines.append(f"- `{item['override_id']}` — {', '.join(item.get('rejection_reasons', [])) or item.get('status', 'rejected')}")
        if not report.rejected_interventions:
            lines.append("- none / لا يوجد")
        lines.extend(["", f"> {report.disclaimer_en}", f"> {report.disclaimer_ar}"])
        return "\n".join(lines) + "\n"

    def write_json(self, report: OverrideReport, output_path: str | Path) -> Path:
        """Write JSON report artifact."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
