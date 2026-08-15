"""Post-implementation verification evaluation for change requests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord

from .change_models import ChangeRequest, ChangeStatus, ChangeType, VerificationResult, VerificationResults, VerificationStatus


class ChangeVerificationEngine:
    """Evaluate supplied verification evidence without running remote probes."""

    SUPPORTED_TYPES = {"command_verification", "connectivity_verification", "service_verification", "routing_verification", "monitoring_verification", "user_verification"}

    def verify(self, request: ChangeRequest, results: Iterable[VerificationResult | Mapping[str, Any]]) -> VerificationResults:
        """Evaluate verification observations and update the change lifecycle."""
        normalized: list[VerificationResult] = []
        for raw in results:
            result = raw if isinstance(raw, VerificationResult) else VerificationResult(str(raw.get("verification_id", "")), str(raw.get("verification_type", "")), str(raw.get("command_or_action", "")), str(raw.get("expected_result", "")), str(raw.get("actual_result", "")), str(raw.get("status", VerificationStatus.NOT_VERIFIABLE.value)), raw.get("executed_at"), tuple(str(item) for item in raw.get("evidence_ids", ())))
            if result.verification_type not in self.SUPPORTED_TYPES:
                raise ValueError(f"unsupported verification type: {result.verification_type}")
            if result.executed_at is None:
                result = VerificationResult(result.verification_id, result.verification_type, result.command_or_action, result.expected_result, result.actual_result, result.status, datetime.now(timezone.utc), result.evidence_ids)
            normalized.append(result)
        if not normalized:
            request.assumptions.append(Assumption(f"{request.change_id}:verification", "not_supplied", "post-change verification cannot be assumed from execution completion", True))
            aggregate = VerificationResults((), VerificationStatus.NOT_VERIFIABLE.value, True, request.change_type == ChangeType.EMERGENCY.value)
        elif any(item.status == VerificationStatus.FAILED.value for item in normalized):
            aggregate = VerificationResults(tuple(normalized), VerificationStatus.FAILED.value, True, request.change_type == ChangeType.EMERGENCY.value)
        elif any(item.status == VerificationStatus.NOT_VERIFIABLE.value for item in normalized):
            aggregate = VerificationResults(tuple(normalized), VerificationStatus.NOT_VERIFIABLE.value, True, request.change_type == ChangeType.EMERGENCY.value)
        elif any(item.status == VerificationStatus.WARNING.value for item in normalized):
            aggregate = VerificationResults(tuple(normalized), VerificationStatus.WARNING.value, False, request.change_type == ChangeType.EMERGENCY.value)
        else:
            aggregate = VerificationResults(tuple(normalized), VerificationStatus.PASSED.value, False, request.change_type == ChangeType.EMERGENCY.value)
        request.verification_results = aggregate
        request.status = ChangeStatus.COMPLETED.value if aggregate.overall_status == VerificationStatus.PASSED.value else ChangeStatus.FAILED.value if aggregate.overall_status == VerificationStatus.FAILED.value else ChangeStatus.VERIFICATION.value
        request.updated_at = datetime.now(timezone.utc)
        request.decision_records.append(DecisionRecord("ChangeVerificationEngine", f"{request.change_id}:verification", aggregate.overall_status, [VerificationStatus.PASSED.value, VerificationStatus.FAILED.value, VerificationStatus.NOT_VERIFIABLE.value], {VerificationStatus.PASSED.value: "selected only when all supplied checks passed", VerificationStatus.NOT_VERIFIABLE.value: "selected when evidence is incomplete"}))
        return aggregate
