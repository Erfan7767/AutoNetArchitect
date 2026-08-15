"""Bilingual incident report rendering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from designers.base_designer import DecisionRecord

from ._common import make_decision, safe_details
from .incident_models import Incident, IncidentReview
from .incident_metrics import IncidentMetrics


class IncidentReporter:
    """Render incident and metrics artifacts without adding unsupported claims."""

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Any] = []

    def individual(self, incident: Incident, *, review: IncidentReview | None = None, language: str = "en") -> dict[str, Any]:
        """Return a complete sanitized individual incident report."""
        if language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        payload = safe_details(incident.model_dump(mode="json"))
        payload["report_metadata"] = {"title": "Incident Report" if language == "en" else "تقرير الحادثة", "automatic_containment_executed": False, "automatic_remediation_executed": False, "review_attached": review is not None}
        if review is not None:
            payload["post_incident_review"] = safe_details(review.model_dump(mode="json"))
        self.decisions.append(make_decision("IncidentReporter", f"{incident.incident_id}:individual-report", "complete_sanitized_report", "preserve incident traceability and governance fields in the report", ["complete_sanitized_report", "summary_only"], {"complete_sanitized_report": "selected", "summary_only": "rejected for audit use"}))
        return payload

    def summary(self, incidents: Sequence[Incident], metrics: IncidentMetrics, *, period: str, language: str = "en") -> dict[str, Any]:
        """Return a weekly or monthly incident summary."""
        title = f"Incident Summary — {period}" if language == "en" else f"ملخص الحوادث — {period}"
        return {"title": title, "period": period, "metrics": safe_details(metrics.model_dump(mode="json")), "incident_ids": [item.incident_id for item in incidents], "severity_counts": metrics.by_severity, "category_counts": metrics.by_category, "governance": {"containment_requires_human_approval": True, "remediation_requires_human_approval": True}}

    def management_dashboard(self, incidents: Sequence[Incident], metrics: IncidentMetrics, *, language: str = "en") -> dict[str, Any]:
        """Return dashboard data with no secret values."""
        return {"title": "Management Dashboard" if language == "en" else "لوحة الإدارة", "open_incidents": [item.incident_id for item in incidents if item.status.value not in {"closed", "cancelled"}], "critical_incidents": [item.incident_id for item in incidents if item.severity.value == "P1"], "metrics": safe_details(metrics.model_dump(mode="json"))}

    def compliance_audit(self, incidents: Sequence[Incident], *, language: str = "en") -> dict[str, Any]:
        """Return traceability and evidence-preservation data without claiming compliance certification."""
        return {"title": "Incident Compliance Evidence Report" if language == "en" else "تقرير أدلة حوكمة الحوادث", "scope": "technical incident records only", "compliance_certification_claim": False, "incidents": [{"incident_id": item.incident_id, "timeline_entries": len(item.timeline), "evidence_references": sorted({evidence for entry in item.timeline for evidence in entry.evidence}), "review_required": item.severity.value in {"P1", "P2"}, "review_present": False} for item in incidents]}

    def to_json(self, payload: Mapping[str, Any], path: str | Path | None = None) -> str:
        """Serialize a report payload to JSON and optionally save atomically."""
        text = json.dumps(safe_details(dict(payload)), indent=2, ensure_ascii=False, default=str) + "\n"
        if path is not None:
            target = Path(path)
            temporary = target.with_suffix(target.suffix + ".tmp")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
        return text
