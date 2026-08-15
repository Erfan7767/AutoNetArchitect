"""Incident report export formats with secret-safe serialization."""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from ._common import safe_details


class IncidentExporter:
    """Export incident artifacts for local review or downstream human-controlled ITSM import."""

    def to_json(self, payload: Mapping[str, Any], path: str | Path | None = None) -> str:
        """Serialize a sanitized JSON artifact."""
        text = json.dumps(safe_details(dict(payload)), indent=2, ensure_ascii=False, default=str) + "\n"
        if path is not None:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(target.suffix + ".tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(target)
        return text

    def to_csv(self, incidents: Sequence[Mapping[str, Any]], path: str | Path | None = None) -> str:
        """Serialize selected incident fields as CSV."""
        fields = ["incident_id", "title", "status", "severity", "priority", "category", "detected_at", "resolved_at", "affected_users_estimate"]
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for item in incidents:
            flat = dict(item)
            for key in ("status", "severity", "priority", "category"):
                value = flat.get(key)
                flat[key] = value.get("value", value) if isinstance(value, Mapping) else value
            writer.writerow(safe_details(flat))
        text = output.getvalue()
        if path is not None:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return text

    def to_pdf(self, payload: Mapping[str, Any], path: str | Path) -> str:
        """Render a simple local PDF from a sanitized JSON payload."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = json.dumps(safe_details(dict(payload)), indent=2, ensure_ascii=False, default=str).splitlines()
        pdf = canvas.Canvas(str(target), pagesize=A4)
        _, height = A4
        y = height - 40
        for line in lines:
            if y < 40:
                pdf.showPage()
                y = height - 40
            pdf.setFont("Helvetica", 8)
            pdf.drawString(36, y, line[:180])
            y -= 11
        pdf.save()
        return str(target)

    def to_itsm(self, incident: Mapping[str, Any], *, system: str) -> dict[str, Any]:
        """Build a human-reviewed ServiceNow/Jira-like import payload without posting it."""
        if system.lower() not in {"servicenow", "jira"}:
            raise ValueError("supported ITSM formats are ServiceNow and Jira")
        item = safe_details(dict(incident))
        return {"format": system.lower(), "external_submission": False, "short_description": item.get("title", ""), "description": item.get("description", ""), "severity": item.get("severity", ""), "priority": item.get("priority", ""), "correlation_id": item.get("incident_id", ""), "raw_incident_reference": item.get("incident_id", "")}

    def timeline_csv(self, incident: Mapping[str, Any], path: str | Path | None = None) -> str:
        """Export a timeline only."""
        timeline = incident.get("timeline", [])
        rows = [{"timestamp": item.get("timestamp", ""), "event_type": item.get("event_type", ""), "description": item.get("description", ""), "performed_by": item.get("performed_by", ""), "automated": item.get("automated", False)} for item in timeline]
        return self.to_csv(rows, path)
