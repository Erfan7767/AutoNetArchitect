"""Reporting for discrepancy and failure memory."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .correction_patterns import CorrectionPattern
from .discrepancy_registry import DiscrepancyRecord
from .failure_memory import FailureMemoryEntry
from .lesson_model import LessonRecord
from .recurrence_detector import RecurrencePattern


class LearningReport(BaseModel):
    """Machine-readable learning-memory summary."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    project_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    discrepancy_count: int
    failure_count: int
    recurring_pattern_count: int
    correction_pattern_count: int
    lesson_count: int
    discrepancies: tuple[dict, ...] = ()
    failures: tuple[dict, ...] = ()
    recurring_patterns: tuple[dict, ...] = ()
    correction_patterns: tuple[dict, ...] = ()
    lessons: tuple[dict, ...] = ()
    published_lesson_ids: tuple[str, ...] = ()
    evidence_gaps: tuple[str, ...] = ()
    consumer_note: str = "Downstream knowledge and benchmarking consumers must use only published lessons and retain source links."


class LearningReporter(BaseDesigner):
    """Generate bilingual learning-memory reports."""

    def __init__(self) -> None:
        """Initialize reporter."""
        super().__init__("LearningReporter")
        self.record_decision("learning_report_policy", "failure_and_evidence_gaps_explicit", "reports retain failures and surface evidence gaps rather than presenting optimistic summaries")

    def generate(self, *, project_id: str, discrepancies: Iterable[DiscrepancyRecord] = (), failures: Iterable[FailureMemoryEntry] = (), recurring_patterns: Iterable[RecurrencePattern] = (), correction_patterns: Iterable[CorrectionPattern] = (), lessons: Iterable[LessonRecord] = (), published_lesson_ids: Iterable[str] = (), report_id: str | None = None) -> LearningReport:
        """Generate a report suitable for human review and downstream consumers."""
        discrepancy_items = tuple(discrepancies)
        failure_items = tuple(failures)
        recurrence_items = tuple(recurring_patterns)
        correction_items = tuple(correction_patterns)
        lesson_items = tuple(lessons)
        evidence_gaps = tuple(dict.fromkeys([f"{item.discrepancy_id}: evidence state {item.evidence_state}" for item in discrepancy_items if item.evidence_state not in {"verified", "partially_verified"}] + [f"{item.lesson_id}: lesson evidence status {item.evidence_status.value}" for item in lesson_items if item.evidence_status.value not in {"verified", "partially_verified"}]))
        report = LearningReport(report_id=report_id or f"LM-{project_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}", project_id=project_id, discrepancy_count=len(discrepancy_items), failure_count=len(failure_items), recurring_pattern_count=len(recurrence_items), correction_pattern_count=len(correction_items), lesson_count=len(lesson_items), discrepancies=tuple(item.model_dump(mode="json") for item in discrepancy_items), failures=tuple(item.model_dump(mode="json") for item in failure_items), recurring_patterns=tuple(item.model_dump(mode="json") for item in recurrence_items), correction_patterns=tuple(item.model_dump(mode="json") for item in correction_items), lessons=tuple(item.model_dump(mode="json") for item in lesson_items), published_lesson_ids=tuple(dict.fromkeys(str(item) for item in published_lesson_ids)), evidence_gaps=evidence_gaps)
        self.record_decision(f"learning_report:{report.report_id}", "generated", "learning report includes discrepancy, failure, recurrence, correction, and evidence-gap state")
        return report

    def to_markdown(self, report: LearningReport) -> str:
        """Render a bilingual learning-memory report."""
        lines = [f"# Discrepancy & Failure Memory Report / تقرير الفروقات وذاكرة الفشل", "", f"**Project / المشروع:** {report.project_id}", f"**Generated / التوليد:** {report.generated_at.isoformat()}", "", "| Metric | Count |", "| --- | ---: |", f"| Discrepancies / الفروقات | {report.discrepancy_count} |", f"| Failures / حالات الفشل | {report.failure_count} |", f"| Recurring patterns / الأنماط المتكررة | {report.recurring_pattern_count} |", f"| Human correction patterns / أنماط التصحيح البشري | {report.correction_pattern_count} |", f"| Lessons / الدروس | {report.lesson_count} |", "", "## Evidence Gaps / فجوات الأدلة", ""]
        if report.evidence_gaps:
            lines.extend(f"- {item}" for item in report.evidence_gaps)
        else:
            lines.append("- none recorded / لا توجد فجوات مسجلة")
        lines.extend(["", "## Recurring Patterns / الأنماط المتكررة", ""])
        if report.recurring_patterns:
            lines.extend(f"- `{item['pattern_id']}` — {item['summary']} — action: {item['required_action']}" for item in report.recurring_patterns)
        else:
            lines.append("- none recorded / لا توجد أنماط مسجلة")
        lines.extend(["", "> Downstream consumers must use published lessons with traceable evidence.", "> يجب على المستهلكين اللاحقين استخدام الدروس المنشورة ذات الأدلة القابلة للتتبع."])
        return "\n".join(lines) + "\n"

    def write_json(self, report: LearningReport, output_path: str | Path) -> Path:
        """Write report JSON."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return target
