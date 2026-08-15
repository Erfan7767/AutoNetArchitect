"""Bilingual incident communications generation without external sending."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord

from ._common import make_assumption, make_decision, safe_details
from .incident_models import Communication, Incident, IncidentSeverity


class CommunicationManager:
    """Generate sanitized communications for technical, management, and user audiences."""

    TYPES = {"initial_notification", "status_update", "escalation_notification", "resolution_notification", "closure_notification"}
    AUDIENCES = {"technical_team", "management", "affected_users", "external_stakeholders"}
    CHANNELS = {"email", "sms", "chat", "status_page"}

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def generate(self, incident: Incident, *, communication_type: str, audience: str, channel: str, language: str = "en", additional_context: Mapping[str, Any] | None = None) -> Communication:
        """Generate a communication artifact; sending remains outside V1."""
        if communication_type not in self.TYPES:
            raise ValueError("unsupported communication type")
        if audience not in self.AUDIENCES:
            raise ValueError("unsupported communication audience")
        if channel not in self.CHANNELS:
            raise ValueError("unsupported communication channel")
        if language not in {"en", "ar"}:
            raise ValueError("language must be en or ar")
        context = dict(additional_context or {})
        severity = incident.severity.value
        if language == "ar":
            subject = f"تحديث حادثة {incident.incident_id} — {incident.title}"
            if communication_type == "initial_notification":
                body = f"تم تسجيل حادثة {severity}. التأثير الحالي: {context.get('impact', 'قيد التقييم')}. سيصدر التحديث التالي وفق مستوى الخدمة المحدد."
            elif communication_type == "resolution_notification":
                body = "تمت استعادة الخدمة وفق الأدلة المتاحة، وتستمر المراقبة قبل الإغلاق النهائي."
            elif communication_type == "closure_notification":
                body = "أُغلقت الحادثة بعد استكمال التحقق والمراجعة المطلوبة."
            else:
                body = f"تحديث حادثة {severity}: الحالة الحالية {incident.status.value}."
        else:
            subject = f"Incident update {incident.incident_id} — {incident.title}"
            if communication_type == "initial_notification":
                body = f"A {severity} incident has been logged. Current impact: {context.get('impact', 'under assessment')}. The next update follows the applicable SLA."
            elif communication_type == "resolution_notification":
                body = "Service recovery has been observed against the available evidence; monitoring continues before final closure."
            elif communication_type == "closure_notification":
                body = "The incident is closed after required verification and review activities were completed."
            else:
                body = f"Incident {severity} update: current state is {incident.status.value}."
        if audience == "affected_users":
            body = self._plain_language(body, language)
        communication = Communication(communication_id=f"COM-{uuid.uuid4()}", communication_type=communication_type, audience=audience, channel=channel, language=language, subject=subject, body=body, sent=False)
        decision = make_decision("CommunicationManager", f"{incident.incident_id}:communication:{communication_type}:{audience}", "generate_unsent_artifact", "V1 generates bilingual artifacts but does not send external notifications automatically", ["generate_unsent_artifact", "send_external_notification"], {"generate_unsent_artifact": "selected", "send_external_notification": "requires a separate human-controlled integration"})
        self.decisions.append(decision)
        return communication

    @staticmethod
    def _plain_language(body: str, language: str) -> str:
        """Keep user-facing text concise and non-technical."""
        if language == "ar":
            return body.replace("الحادثة", "المشكلة").replace("الأدلة المتاحة", "المعلومات المتاحة")
        return body.replace("evidence", "available information").replace("incident", "service issue")
