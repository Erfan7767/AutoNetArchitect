"""Diagnostic report generation for JSON and bilingual Markdown output."""

from __future__ import annotations

import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from typing import Any

from designers.base_designer import Assumption, DecisionRecord

from .models import DiagnosticResult


class DiagnosticReporter:
    """Render a diagnostic result without adding unsupported claims."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def to_dict(self, result: DiagnosticResult) -> dict[str, Any]:
        """Return the complete JSON-safe report structure."""
        payload = result.model_dump(mode="json")
        payload["report_metadata"] = {"production_safe_claim": False, "diagnostic_confidence_requires_evidence": True, "write_commands_executed": False}
        self.decisions.append(DecisionRecord("DiagnosticReporter", f"report:{result.diagnostic_id}", "json_and_markdown_ready", "render all result sections without altering evidence or confidence", ["json_and_markdown_ready", "summary_only"], {"json_and_markdown_ready": "selected", "summary_only": "rejected because traceability is required"}))
        return payload

    def to_json(self, result: DiagnosticResult, path: str | Path | None = None) -> str:
        """Render JSON and optionally write it atomically."""
        text = json.dumps(self.to_dict(result), indent=2, ensure_ascii=False, default=str) + "\n"
        if path is not None:
            target = Path(path)
            temporary = target.with_suffix(target.suffix + ".tmp")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
        return text

    def to_pdf(self, result: DiagnosticResult, path: str | Path) -> str:
        """Render a plain-text diagnostic PDF and return its path."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        document = self.to_markdown(result, bilingual=True)
        pdf = canvas.Canvas(str(target), pagesize=A4)
        width, height = A4
        cursor_y = height - 40
        for line in document.splitlines():
            if cursor_y < 40:
                pdf.showPage()
                cursor_y = height - 40
            pdf.setFont("Helvetica", 8)
            pdf.drawString(36, cursor_y, line[:180])
            cursor_y -= 11
        pdf.save()
        return str(target)

    def to_markdown(self, result: DiagnosticResult, *, bilingual: bool = True) -> str:
        """Render the required diagnostic sections in English and Arabic headings."""
        root = result.root_cause_analysis
        lines = [f"# Diagnostic Report / تقرير التشخيص: {result.diagnostic_id}", "", "> This report is evidence-bounded. It does not claim confirmed production safety or execute write commands. / هذا التقرير مقيد بالأدلة ولا ينفذ أوامر تعديل.", "", "## 1. Issue Summary / ملخص المشكلة", f"- Symptom / العرض: {result.symptom_input.symptom_description}", f"- Severity / الشدة: {result.symptom_input.severity.value}", f"- Scope / النطاق: {result.symptom_input.affected_scope.scope_type.value} {result.symptom_input.affected_scope.identifiers}", f"- Status / الحالة: {result.status.value}", "", "## 2. Diagnostic Timeline / الخط الزمني"]
        lines.extend(f"- {event.timestamp.isoformat()} — {event.event_type}: {event.description}" for event in result.timeline)
        lines.extend(["", "## 3. Evidence Collected / الأدلة المجمعة"])
        lines.extend(f"- {item.evidence_id}: source={item.source.value}, confidence={item.confidence:.2f}, notes={item.notes or 'none'}" for item in result.evidence)
        lines.extend(["", "## 4. Hypotheses Tested / الفرضيات المختبرة"])
        lines.extend(f"- {item.hypothesis_id}: status={item.status}, confidence={item.confidence:.2f}, rationale={item.rationale}" for item in result.hypothesis_evaluations)
        lines.extend(["", "## 5. Root Cause Analysis / تحليل السبب الجذري", f"- Root cause / السبب المحتمل: {root.root_cause}", f"- Confidence / الثقة: {root.root_cause_confidence:.2f} ({root.confidence_level})", f"- Classification / التصنيف: {root.root_cause_classification.value}", f"- Uncertainties / نقاط عدم اليقين: {root.unresolved_uncertainties or ['none recorded']}" , "", "## 6. Impact Assessment / تقييم الأثر", f"- Service impact: {result.impact_assessment.service_impact}", f"- User impact: {result.impact_assessment.user_impact}", f"- Security impact: {result.impact_assessment.security_impact}", "", "## 7. Remediation Recommendation / توصية الإصلاح"])
        lines.extend(f"- {step.description}; risk={step.risk_level}; change_request={step.requires_change_request}; maintenance_window={step.requires_maintenance_window}" for step in result.remediation_plan.steps)
        lines.extend(["", "## 8. Escalation Recommendation / توصية التصعيد", f"- Required: {result.escalation.required}", f"- Targets: {[item.value for item in result.escalation.targets]}", f"- Reasons: {result.escalation.reasons or ['none recorded']}", "", "## 9. Related Changes / التغييرات المرتبطة"])
        lines.extend(f"- {change}" for change in result.related_changes) if result.related_changes else lines.append("- None supplied / لم تقدم تغييرات مرتبطة")
        lines.extend(["", "## 10. Known Issues Match / مطابقة المشاكل المعروفة"])
        lines.extend(f"- {issue}" for issue in result.known_issue_matches) if result.known_issue_matches else lines.append("- None supplied / لم توجد مطابقة")
        lines.extend(["", "## 11. Appendix: Raw Evidence / الملحق: الأدلة الخام", "- Raw evidence is retained in the structured artifact and remains redacted where required. / الأدلة الخام محفوظة في artifact المهيكل ومُنقّحة عند الحاجة.", "", "## Governance Notes / ملاحظات الحوكمة", f"- Write commands executed / أوامر تعديل منفذة: False", f"- Evidence IDs / معرفات الأدلة: {result.evidence_ids}", f"- Limitations / القيود: {result.limitations or ['none recorded']}"])
        return "\n".join(lines) + "\n"
