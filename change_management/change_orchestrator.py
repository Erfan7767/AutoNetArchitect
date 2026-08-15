"""End-to-end governed change lifecycle orchestration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Callable, Iterable, Mapping, Sequence

from .change_approval_engine import ApprovalEvaluation, ApprovalRequirements, ChangeApprovalEngine
from .change_classifier import ChangeClassification, ChangeClassifier
from .change_communication_generator import ChangeCommunicationGenerator, CommunicationMessage
from .change_execution_tracker import ChangeExecutionTracker, ExecutionSummary
from .change_history import ChangeHistory
from .change_impact_analyzer import ChangeImpactAnalyzer
from .change_models import (
    Approval,
    ChangeLifecycle,
    ChangeRequest,
    ChangeStatus,
    ConfigChange,
    DeviceRef,
    ServiceRef,
    SiteRef,
    VerificationResult,
)
from .change_plan_builder import ChangePlanBuilder
from .change_request_manager import ChangeRequestManager
from .change_risk_analyzer import ChangeRiskAnalyzer
from .change_rollback_planner import ChangeRollbackPlanner
from .change_schedule_manager import ChangeScheduleManager
from .change_verification_engine import ChangeVerificationEngine


class ChangeOrchestrator:
    """Coordinate local change governance without assuming an external ITSM."""

    def __init__(self) -> None:
        """Create the complete V1 local orchestration graph."""
        self.history = ChangeHistory()
        self.requests = ChangeRequestManager(history_recorder=self._history_adapter)
        self.classifier = ChangeClassifier()
        self.risk_analyzer = ChangeRiskAnalyzer()
        self.impact_analyzer = ChangeImpactAnalyzer()
        self.plan_builder = ChangePlanBuilder()
        self.rollback_planner = ChangeRollbackPlanner()
        self.approvals = ChangeApprovalEngine()
        self.schedule_manager = ChangeScheduleManager()
        self.execution = ChangeExecutionTracker()
        self.verification = ChangeVerificationEngine()
        self.communication = ChangeCommunicationGenerator()

    def create_request(self, *args: Any, **kwargs: Any) -> ChangeRequest:
        """Create a draft request."""
        return self.requests.create(*args, **kwargs)

    def submit(self, change_id: str) -> ChangeRequest:
        """Submit a draft request."""
        return self.requests.submit(change_id)

    def classify(self, change_id: str, **signals: Any) -> ChangeClassification:
        """Classify only after submission."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.SUBMITTED.value}, "classification")
        return self.classifier.classify(request, **signals)

    def assess_risk(self, change_id: str, **signals: Any):
        """Assess risk only after classification."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.SUBMITTED.value, ChangeStatus.RISK_ASSESSED.value}, "risk assessment")
        return self.risk_analyzer.analyze(request, **signals)

    def assess_impact(self, change_id: str, **signals: Any):
        """Assess impact only after risk assessment."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.RISK_ASSESSED.value}, "impact assessment")
        return self.impact_analyzer.analyze(request, **signals)

    def build_plans(self, change_id: str, *, validator: Callable[[str, Sequence[str]], bool] | None = None, step_duration: timedelta | None = None, backup_evidence_ids: Sequence[str] = (), **rollback_options: Any):
        """Build implementation and rollback plans after risk and impact."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.IMPACT_ASSESSED.value}, "plan building")
        implementation = self.plan_builder.build(request, validator=validator, step_duration=step_duration)
        rollback = self.rollback_planner.build(request, backup_evidence_ids=backup_evidence_ids, step_duration=step_duration, **rollback_options)
        request.status = ChangeStatus.PLAN_COMPLETE.value
        return implementation, rollback

    def request_approvals(self, change_id: str, *, sector: str = "general", clinical_sensitive: bool = False) -> tuple[ApprovalRequirements, ApprovalEvaluation]:
        """Move a complete plan to approval evaluation."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.PLAN_COMPLETE.value}, "approval request")
        requirements = self.approvals.requirements(request, sector=sector, clinical_sensitive=clinical_sensitive)
        request.status = ChangeStatus.PENDING_APPROVAL.value
        evaluation = self.approvals.evaluate(request, requirements.required_roles)
        if requirements.pre_approved and not requirements.required_roles:
            request.status = ChangeStatus.APPROVED.value
            evaluation = ApprovalEvaluation("approved", (), (), (), ())
        return requirements, evaluation

    def record_approval(self, change_id: str, approval: Approval, required_roles: Sequence[str]) -> ApprovalEvaluation:
        """Record one approval and update status when all roles approve."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.PENDING_APPROVAL.value}, "approval recording")
        evaluation = self.approvals.record(request, approval)
        if tuple(sorted(required_roles)) != tuple(sorted(evaluation.required_roles)):
            evaluation = self.approvals.evaluate(request, required_roles)
        if evaluation.state in {"approved", "approved_with_conditions"}:
            request.status = ChangeStatus.APPROVED.value
        return evaluation

    def schedule(self, change_id: str, window, **options: Any) -> ChangeRequest:
        """Schedule only an approved request."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.APPROVED.value}, "scheduling")
        return self.schedule_manager.schedule(request, window, **options)

    def start_execution(self, change_id: str, *, actor: str) -> ExecutionSummary:
        """Start execution tracking for a scheduled request."""
        request = self.requests.get(change_id)
        summary = self.execution.start(request, actor=actor)
        self._history_adapter(change_id, "execution_started", {"actor": actor})
        return summary

    def update_step(self, change_id: str, step_number: int, step_status: str, *, executed_by: str, actual_output: str = "", matches_expected: bool | None = None, notes: str = "") -> ExecutionSummary:
        """Append a step execution event."""
        request = self.requests.get(change_id)
        summary = self.execution.update_step(request, step_number, step_status, executed_by=executed_by, actual_output=actual_output, matches_expected=matches_expected, notes=notes)
        self._history_adapter(change_id, "step_execution", {"step_number": step_number, "step_status": step_status, "executed_by": executed_by})
        return summary

    def verify(self, change_id: str, results: Iterable[VerificationResult | Mapping[str, Any]]):
        """Evaluate post-change verification evidence."""
        request = self.requests.get(change_id)
        self._require(request, {ChangeStatus.VERIFICATION.value, ChangeStatus.FAILED.value}, "verification")
        output = self.verification.verify(request, results)
        self._history_adapter(change_id, "verification", {"status": output.overall_status})
        return output

    def close(self, change_id: str, closure_code: str, *, lessons_learned: str = "") -> ChangeRequest:
        """Close a terminal request."""
        return self.requests.close(change_id, closure_code, lessons_learned=lessons_learned)

    def communications(self, change_id: str, stage: str, recipients: Iterable[str], *, language: str = "both") -> tuple[CommunicationMessage, ...]:
        """Generate local communications for a lifecycle stage."""
        return self.communication.generate(self.requests.get(change_id), stage, recipients, language=language)

    def lifecycle(self, change_id: str) -> ChangeLifecycle:
        """Emit a lifecycle artifact with completed steps and next actions."""
        request = self.requests.get(change_id)
        completed: list[str] = []
        next_steps: list[str] = []
        if request.status in {ChangeStatus.DRAFT.value}:
            next_steps.append("submit")
        if request.status == ChangeStatus.SUBMITTED.value:
            next_steps.append("classify")
        if request.status == ChangeStatus.RISK_ASSESSED.value:
            next_steps.append("assess_impact")
        if request.status == ChangeStatus.IMPACT_ASSESSED.value:
            next_steps.append("build_plans")
        if request.status == ChangeStatus.PLAN_COMPLETE.value:
            next_steps.append("request_approvals")
        if request.status == ChangeStatus.PENDING_APPROVAL.value:
            next_steps.append("record_approvals")
        if request.status == ChangeStatus.APPROVED.value:
            next_steps.append("schedule")
        if request.status == ChangeStatus.SCHEDULED.value:
            next_steps.append("start_execution")
        if request.status in {ChangeStatus.IN_PROGRESS.value}:
            next_steps.append("update_steps")
        if request.status == ChangeStatus.VERIFICATION.value:
            next_steps.append("verify")
        if request.status == ChangeStatus.COMPLETED.value:
            completed.append("verification")
            next_steps.append("close")
        return ChangeLifecycle(request.change_id, request.status, tuple(completed), tuple(next_steps), bool(not request.assumptions or all(getattr(item, "requires_validation", True) is False for item in request.assumptions)), tuple(getattr(item, "decision_id", "") for item in request.decision_records), tuple(getattr(item, "key", "") for item in request.assumptions), tuple(request.history_ids), False)

    def _require(self, request: ChangeRequest, allowed: set[str], action: str) -> None:
        """Enforce lifecycle prerequisites."""
        if request.status not in allowed:
            raise ValueError(f"{action} requires status in {sorted(allowed)}, current={request.status}")

    def _history_adapter(self, change_id: str, event: str, details: Mapping[str, Any]) -> str:
        """Record a local hash-chained history event."""
        entry = self.history.record(change_id, event, "change_orchestrator", details)
        return entry.history_id
