"""Governance gates for operational drift and remediation actions."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping

from log_redaction.redacting_filter import RedactingFilter

from .drift_detector import DriftReport, DriftSeverity


RemediationDriver = Callable[[Mapping[str, Any]], Mapping[str, Any]]


@dataclass(frozen=True)
class GovernanceDecision:
    """Decision about whether an operational action may proceed."""

    decision_id: str
    allowed: bool
    action: str
    risk: str
    gate: str
    reasons: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a governance decision."""
        return asdict(self) | {"reasons": list(self.reasons), "required_human_inputs": list(self.required_human_inputs), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class RemediationResult:
    """Result of a proposed or explicitly approved remediation attempt."""

    decision: GovernanceDecision
    executed: bool
    state: str
    output: str = ""
    provider_reference: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize remediation metadata without raw secrets."""
        return asdict(self) | {"decision": self.decision.to_dict(), "evidence_ids": list(self.evidence_ids)}


class OperationalGovernance:
    """Apply explicit approval and audit gates before any remediation driver call."""

    def __init__(self, *, audit_trail: Any | None = None) -> None:
        """Create a governance evaluator with optional audit integration."""
        self.audit_trail = audit_trail

    def evaluate(self, decision_id: str, report: DriftReport, *, approval_reference: str = "", production_requested: bool = False) -> GovernanceDecision:
        """Evaluate a remediation request without executing it."""
        reasons: list[str] = []
        required: list[str] = []
        if not report.read_only:
            reasons.append("drift report is not marked read-only")
        if report.severity == DriftSeverity.NONE.value:
            return GovernanceDecision(decision_id, False, "no_remediation", "none", "allow_read_only", ("no drift was detected",), (), report.evidence_ids)
        if report.severity == DriftSeverity.UNKNOWN.value:
            reasons.append("drift severity is unknown and cannot be safely remediated")
            required.append("verified_drift_evidence")
        if report.severity in {DriftSeverity.HIGH.value, DriftSeverity.CRITICAL.value} and not approval_reference:
            reasons.append("high-risk production drift requires explicit approval before remediation")
            required.append("approval_reference")
        if approval_reference and not approval_reference.startswith("approval://"):
            reasons.append("approval reference must use the approval:// scheme")
            required.append("approval_reference")
        if production_requested and not approval_reference:
            reasons.append("production remediation requires explicit approval")
            required.append("approval_reference")
        allowed = not reasons
        risk = report.severity
        gate = "allow_with_approval" if allowed else "blocked"
        return GovernanceDecision(decision_id, allowed, "remediate_drift", risk, gate, tuple(dict.fromkeys(reasons)), tuple(dict.fromkeys(required)), report.evidence_ids)

    def remediate(self, decision_id: str, report: DriftReport, *, approval_reference: str = "", production_requested: bool = False, driver: RemediationDriver | None = None) -> RemediationResult:
        """Execute only an explicitly approved, governed remediation callback."""
        decision = self.evaluate(decision_id, report, approval_reference=approval_reference, production_requested=production_requested)
        if not decision.allowed:
            result = RemediationResult(decision, False, "blocked", evidence_ids=report.evidence_ids)
            self._audit(result)
            return result
        if driver is None:
            blocked = GovernanceDecision(decision.decision_id, False, decision.action, decision.risk, "blocked", ("remediation driver is not configured",), ("remediation_driver",), decision.evidence_ids)
            result = RemediationResult(blocked, False, "blocked", evidence_ids=report.evidence_ids)
            self._audit(result)
            return result
        payload = {"operation": "remediate_drift", "decision_id": decision_id, "approval_reference": approval_reference, "production_requested": production_requested, "report_id": report.report_id, "operational_sot_record_id": report.operational_sot_record_id, "drift_severity": report.severity, "items": [{"target_id": item.target_id, "path": item.path, "severity": item.severity, "status": item.status, "evidence_ids": list(item.evidence_ids)} for item in report.items], "evidence_ids": list(report.evidence_ids)}
        try:
            response = dict(driver(payload))
            raw = RedactingFilter.sanitize_value(response.get("output", ""))
            output = raw if isinstance(raw, str) else str(raw)
            state = "executed" if str(response.get("state", response.get("status", ""))).lower() in {"success", "successful", "executed", "ok"} else "failed"
            evidence = tuple(dict.fromkeys(report.evidence_ids + tuple(str(item) for item in response.get("evidence_ids", ()))))
            result = RemediationResult(decision, True, state, output, str(response.get("provider_reference", "")), evidence)
        except Exception:
            result = RemediationResult(decision, True, "failed", "remediation driver failed without exposing runtime details", evidence_ids=report.evidence_ids)
        self._audit(result)
        return result

    def preview(self, decision_id: str, report: DriftReport) -> RemediationResult:
        """Return a non-executing remediation preview."""
        decision = GovernanceDecision(decision_id, False, "remediate_drift_preview", report.severity, "review_only", ("preview-only path; no remediation was executed",), (), report.evidence_ids)
        result = RemediationResult(decision, False, "preview_only", "no remediation driver invoked", evidence_ids=report.evidence_ids)
        self._audit(result)
        return result

    def _audit(self, result: RemediationResult) -> None:
        """Record only governance metadata and sanitized driver output."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("operations.remediation", "operational_governance", {"decision_id": result.decision.decision_id, "action": result.decision.action, "risk": result.decision.risk, "gate": result.decision.gate, "executed": result.executed, "state": result.state, "evidence_ids": list(result.evidence_ids)}, outcome=result.state)
