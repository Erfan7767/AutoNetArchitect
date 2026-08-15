"""Emergency change handling with abbreviated but auditable controls."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Sequence

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeRequest, ChangeType


@dataclass(frozen=True)
class EmergencyAssessment:
    """Emergency declaration and mandatory follow-up controls."""

    change_id: str
    allowed_to_start: bool
    justification: str
    criteria: tuple[str, ...]
    required_controls: tuple[str, ...]
    documentation_due: datetime
    review_due: datetime
    reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize emergency assessment."""
        return asdict(self) | {"criteria": list(self.criteria), "required_controls": list(self.required_controls), "documentation_due": self.documentation_due.isoformat(), "review_due": self.review_due.isoformat(), "reasons": list(self.reasons)}


class EmergencyChangeHandler:
    """Enforce V1 emergency criteria and post-implementation review."""

    VALID_CRITERIA = {"service_outage", "active_security_breach", "immediate_regulatory_deadline"}

    def declare(
        self,
        request: ChangeRequest,
        *,
        justification: str,
        criteria: Sequence[str],
        on_call_approval: bool,
        backup_evidence_ids: Sequence[str] = (),
        max_scope: int = 5,
        now: datetime | None = None,
    ) -> EmergencyAssessment:
        """Declare an emergency change and return start permission."""
        current = now or datetime.now(timezone.utc)
        selected = tuple(dict.fromkeys(str(item) for item in criteria))
        reasons: list[str] = []
        if request.change_type != ChangeType.EMERGENCY.value:
            reasons.append("request change_type is not emergency")
        if not justification:
            reasons.append("emergency justification is missing")
        if not selected or any(item not in self.VALID_CRITERIA for item in selected):
            reasons.append("criteria must identify outage, active security breach, or immediate regulatory deadline")
        if not on_call_approval:
            reasons.append("recorded on-call manager approval is missing")
        if len(request.affected_devices) > max_scope:
            reasons.append("emergency scope exceeds the configured maximum")
        if not backup_evidence_ids:
            reasons.append("backup evidence is missing")
        required = ("mandatory backup verification", "recorded on-call approval", "post-implementation documentation within 24 hours", "post-implementation review within 72 hours", "retrospective and root-cause analysis")
        assessment = EmergencyAssessment(request.change_id, not reasons, justification, selected, required, current + timedelta(hours=24), current + timedelta(hours=72), tuple(reasons))
        request.decision_records.append(DecisionRecord("EmergencyChangeHandler", f"{request.change_id}:emergency", assessment.allowed_to_start, [True, False], {"True": "all emergency controls supplied", "False": "one or more emergency controls missing"}))
        if not backup_evidence_ids:
            request.assumptions.append(Assumption(f"{request.change_id}:emergency_backup", "missing", "emergency changes require a current backup before implementation", True))
        return assessment
