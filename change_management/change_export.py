"""Export change records to local and future-integration formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Iterable, Mapping

from log_redaction.redacting_filter import RedactingFilter

from .change_models import ChangeRequest


class ChangeExport:
    """Export complete change records without external side effects."""

    def as_dict(self, request: ChangeRequest) -> dict[str, Any]:
        """Return a redacted generic representation."""
        sanitized = RedactingFilter.sanitize_value(request.to_dict())
        if not isinstance(sanitized, dict):
            raise ValueError("change export must remain a mapping")
        return sanitized

    def json(self, request: ChangeRequest, *, indent: int = 2) -> str:
        """Export one request as JSON."""
        return json.dumps(self.as_dict(request), indent=indent, sort_keys=True, default=str, ensure_ascii=False) + "\n"

    def csv(self, requests: Iterable[ChangeRequest]) -> str:
        """Export change summary rows as CSV."""
        output = io.StringIO()
        fields = ("change_id", "title", "requester", "change_type", "change_category", "priority", "status", "risk_level", "impact_class", "created_at", "updated_at")
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for request in requests:
            writer.writerow({"change_id": request.change_id, "title": request.title, "requester": request.requester, "change_type": request.change_type, "change_category": request.change_category, "priority": request.priority, "status": request.status, "risk_level": request.risk_assessment.risk_level, "impact_class": request.impact_assessment.impact_class, "created_at": request.created_at.isoformat(), "updated_at": request.updated_at.isoformat()})
        return output.getvalue()

    def pdf(self, request: ChangeRequest) -> bytes:
        """Export a concise formal PDF without resolving secrets."""
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        document = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        y = height - 48
        document.setFont("Helvetica-Bold", 14)
        document.drawString(48, y, f"AutoNetArchitect Change Report: {request.change_id}")
        document.setFont("Helvetica", 10)
        y -= 24
        lines = (f"Title: {request.title}", f"Requester: {request.requester}", f"Type: {request.change_type}", f"Category: {request.change_category}", f"Priority: {request.priority}", f"Status: {request.status}", f"Risk: {request.risk_assessment.risk_level}", f"Impact: {request.impact_assessment.impact_class}", f"Verification: {request.verification_results.overall_status}", "Production execution is governed by change-control policy.")
        for line in lines:
            document.drawString(48, y, line[:140])
            y -= 16
        document.save()
        return buffer.getvalue()

    def external(self, request: ChangeRequest, target: str = "generic") -> dict[str, Any]:
        """Create integration-ready ServiceNow, Jira, or generic field mapping."""
        payload = self.as_dict(request)
        normalized = target.lower()
        if normalized == "servicenow":
            return {"short_description": request.title, "description": request.description, "requested_by": request.requester, "category": request.change_category, "priority": request.priority, "state": request.status, "u_autonetarchitect_change_id": request.change_id, "u_risk_level": request.risk_assessment.risk_level, "u_payload": payload}
        if normalized == "jira":
            return {"summary": request.title, "description": request.description, "reporter": request.requester, "issuetype": {"name": "Change"}, "priority": {"name": request.priority}, "labels": ["autonetarchitect", request.change_category], "external_id": request.change_id, "fields": payload}
        if normalized != "generic":
            raise ValueError("unsupported export target")
        return {"system": "generic_itsm", "external_integration_required": True, "change": payload}
