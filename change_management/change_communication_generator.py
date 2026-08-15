"""Bilingual communication generation for change lifecycle stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from .change_models import ChangeRequest


@dataclass(frozen=True)
class CommunicationMessage:
    """Generated message ready for human review and local export."""

    message_id: str
    change_id: str
    stage: str
    language: str
    recipients: tuple[str, ...]
    subject: str
    body: str
    scheduled_for: datetime | None = None
    sent: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize message."""
        return asdict(self) | {"recipients": list(self.recipients), "scheduled_for": self.scheduled_for.isoformat() if self.scheduled_for else None}


class ChangeCommunicationGenerator:
    """Generate Arabic and English notifications without invoking a messaging service."""

    STAGES = {"pre_change", "start", "completion", "failure"}

    def generate(self, request: ChangeRequest, stage: str, recipients: Iterable[str], *, language: str = "both", scheduled_for: datetime | None = None) -> tuple[CommunicationMessage, ...]:
        """Generate one or two localized messages for a lifecycle stage."""
        if stage not in self.STAGES:
            raise ValueError("unsupported communication stage")
        recipient_tuple = tuple(dict.fromkeys(str(item) for item in recipients if str(item)))
        if not recipient_tuple:
            raise ValueError("at least one recipient reference is required")
        languages = ("ar", "en") if language == "both" else (language,)
        if any(item not in {"ar", "en"} for item in languages):
            raise ValueError("language must be ar, en, or both")
        result: list[CommunicationMessage] = []
        for selected in languages:
            subject, body = self._content(request, stage, selected)
            result.append(CommunicationMessage(f"{request.change_id}:communication:{stage}:{selected}", request.change_id, stage, selected, recipient_tuple, subject, body, scheduled_for, False))
        return tuple(result)

    @staticmethod
    def _content(request: ChangeRequest, stage: str, language: str) -> tuple[str, str]:
        """Render bounded bilingual content from request fields."""
        if language == "ar":
            subjects = {"pre_change": f"إشعار تغيير الشبكة {request.change_id}", "start": f"بدء التغيير {request.change_id}", "completion": f"اكتمال التغيير {request.change_id}", "failure": f"فشل التغيير {request.change_id}"}
            bodies = {"pre_change": f"سيتم تنفيذ التغيير {request.title}. الوصف: {request.description}. الأثر المتوقع: {request.impact_assessment.impact_class}.", "start": f"بدأ تنفيذ التغيير {request.change_id}. يجب اتباع خطة التنفيذ والتحقق.", "completion": f"اكتمل التغيير {request.change_id} بحالة تحقق {request.verification_results.overall_status}.", "failure": f"فشل التغيير {request.change_id}. يجب مراجعة نتائج التحقق وخطة التراجع."}
        else:
            subjects = {"pre_change": f"Network change notification {request.change_id}", "start": f"Change started {request.change_id}", "completion": f"Change completed {request.change_id}", "failure": f"Change failure {request.change_id}"}
            bodies = {"pre_change": f"The change {request.title} is planned. Description: {request.description}. Expected impact: {request.impact_assessment.impact_class}.", "start": f"Change {request.change_id} has started. Follow the approved implementation and verification plan.", "completion": f"Change {request.change_id} completed with verification status {request.verification_results.overall_status}.", "failure": f"Change {request.change_id} failed. Review verification results and the rollback plan."}
        return subjects[stage], bodies[stage]
