"""Governed deployment orchestration for dry-run and approved real execution."""

from __future__ import annotations

from dataclasses import replace
import hashlib
from typing import Any, Callable, Mapping

from audit.audit_trail import AuditTrail
from governance import AccountabilityMatrix, CheckpointRecord, CheckpointType, DecisionClass, RiskClass, SeparationOfDutiesPolicy, SignoffPolicy
from supervised_mode import ApprovalGate, BlockGate, ReviewGate, SupervisionContext, SupervisionContextManager, SupervisionPolicy, SupervisionDecision
from review_control import CheckpointRecord as MandatoryReviewRecord, NoGoBlocker, ReadinessGate

from .api_deployer import APIDeployer
from .deployer_common import BackupProvider, DeploymentDriver
from .deployment_models import DeploymentOperation, DeploymentRequest, DeploymentResult, DeploymentState
from .deployment_result_handler import DeploymentResultHandler
from .netconf_deployer import NETCONFDeployer
from .rollback_manager import RollbackAssessment, RollbackManager, RollbackRequest
from .safety_classifier import SafetyAssessment, SafetyClassifier
from .ssh_deployer import SSHDeployer


VerificationProvider = Callable[[DeploymentRequest, DeploymentOperation], Any]


class DeploymentOrchestrator:
    """Coordinate deployment gates before any transport driver is invoked."""

    def __init__(self, *, audit_trail: AuditTrail | None = None, verification_provider: VerificationProvider | None = None, rollback_manager: RollbackManager | None = None, governance_policy: SignoffPolicy | None = None, supervision_context: SupervisionContext | None = None, supervision_policy: SupervisionPolicy | None = None) -> None:
        """Create a deployment orchestrator with optional governance and supervision integrations."""
        self.audit_trail = audit_trail
        self.verification_provider = verification_provider
        self.rollback_manager = rollback_manager or RollbackManager()
        self.governance_policy = governance_policy
        self.supervision_context = supervision_context
        self.supervision_policy = supervision_policy or SupervisionPolicy()
        self.supervision_context_manager = SupervisionContextManager(audit_trail=audit_trail)
        supervision_signoff = governance_policy or SignoffPolicy()
        self.review_gate = ReviewGate(signoff_policy=supervision_signoff, context_manager=self.supervision_context_manager)
        self.approval_gate = ApprovalGate(signoff_policy=supervision_signoff, context_manager=self.supervision_context_manager)
        self.block_gate = BlockGate(context_manager=self.supervision_context_manager)
        self.readiness_gate = ReadinessGate()
        self.accountability_matrix = AccountabilityMatrix()
        self.separation_policy = SeparationOfDutiesPolicy()
        self.safety_classifier = SafetyClassifier()
        self.result_handler = DeploymentResultHandler()
        self.deployers = {"ssh": SSHDeployer(), "netconf": NETCONFDeployer(), "api": APIDeployer()}

    def deploy(self, request: DeploymentRequest, *, driver: DeploymentDriver | None = None, backup_provider: BackupProvider | None = None, verification_report: Any = None, rollback_request: RollbackRequest | None = None, rollback_assessment: RollbackAssessment | None = None) -> DeploymentResult:
        """Evaluate gates, run dry-run or real transport, then process evidence."""
        preflight = self._preflight(request)
        if preflight is not None:
            self._audit(request, preflight)
            return preflight
        supervision_block = self._supervised_preflight(request)
        if supervision_block is not None:
            self._audit(request, supervision_block)
            return supervision_block
        review_control_block = self._review_control_preflight(request)
        if review_control_block is not None:
            self._audit(request, review_control_block)
            return review_control_block
        governance_block = self._governance_preflight(request)
        if governance_block is not None:
            self._audit(request, governance_block)
            return governance_block
        safety = self._safety(request)
        if not safety.allowed:
            state = DeploymentState.BLOCKED_POLICY.value
            if "human_change_approval" in safety.required_approvals or "production_change_control" in safety.required_approvals or any("approval" in reason for reason in safety.reasons):
                state = DeploymentState.BLOCKED_APPROVAL.value
            operation = self._operation(request, state, safety.reasons + ("deployment safety policy did not allow the requested path",))
            result = self.result_handler.handle(operation)
            self._audit(request, result)
            return result
        effective_request = request
        if not request.dry_run:
            effective_request, backup_block = self._prepare_backup(request, backup_provider)
            if backup_block is not None:
                self._audit(request, backup_block)
                return backup_block
        deployer = self.deployers.get(request.transport.lower())
        if deployer is None:
            operation = self._operation(request, DeploymentState.BLOCKED_UNSUPPORTED.value, (f"unsupported deployment transport: {request.transport}",))
            result = self.result_handler.handle(operation)
            self._audit(request, result)
            return result
        operation = deployer.deploy(effective_request, driver=driver, backup_provider=None)
        if verification_report is None and operation.state == DeploymentState.EXECUTED.value and self.verification_provider is not None:
            verification_report = self.verification_provider(effective_request, operation)
        if rollback_assessment is None and rollback_request is not None and operation.state == DeploymentState.FAILED.value:
            rollback_assessment = self.rollback_manager.assess(rollback_request)
        result = self.result_handler.handle(operation, verification=verification_report, rollback=rollback_assessment)
        self._audit(effective_request, result)
        if rollback_assessment is not None:
            self._audit_rollback(effective_request, rollback_assessment)
        return result

    def classify(self, request: DeploymentRequest) -> SafetyAssessment:
        """Expose the pre-execution safety classification."""
        return self._safety(request)

    def _preflight(self, request: DeploymentRequest) -> DeploymentResult | None:
        """Block invalid project state and unresolved human execution inputs."""
        if not request.project_valid:
            operation = self._operation(request, DeploymentState.BLOCKED_INVALID_PROJECT_STATE.value, ("project state is invalid or unresolved",))
            return self.result_handler.handle(operation)
        if request.unresolved_human_inputs:
            operation = self._operation(request, DeploymentState.BLOCKED_HUMAN_DATA.value, tuple(request.unresolved_human_inputs))
            return self.result_handler.handle(operation)
        return None

    def _supervised_preflight(self, request: DeploymentRequest) -> DeploymentResult | None:
        """Run the registered supervised checkpoint before deployment execution."""
        if not request.supervised_mode or self.supervision_context is None:
            return None
        evaluation = self.supervision_policy.evaluate(request.supervision_checkpoint_id, self.supervision_context, evidence_ids=request.evidence_ids, mutating=not request.dry_run)
        if evaluation.decision == SupervisionDecision.BLOCKED:
            self.supervision_context, result = self.block_gate.evaluate(evaluation, self.supervision_context, evidence_ids=request.evidence_ids)
            operation = self._operation(request, DeploymentState.BLOCKED_POLICY.value, result.reasons or ("supervised checkpoint is blocked",))
            return self.result_handler.handle(operation)
        if evaluation.decision == SupervisionDecision.REQUIRES_REVIEW:
            self.supervision_context, result = self.review_gate.evaluate(evaluation, self.supervision_context, reviewer_id=request.supervision_reviewer_id or None, reviewer_role=request.supervision_reviewer_role or None, action=request.supervision_reviewer_action, rationale=request.supervision_reviewer_rationale, reference=request.supervision_reviewer_reference, evidence_ids=request.evidence_ids)
            if not result.continued:
                operation = self._operation(request, DeploymentState.BLOCKED_APPROVAL.value, result.reasons or ("supervised review is required",))
                return self.result_handler.handle(operation)
        if evaluation.decision == SupervisionDecision.REQUIRES_APPROVAL:
            self.supervision_context, result = self.approval_gate.evaluate(evaluation, self.supervision_context, approver_id=request.supervision_approver_id or None, approver_role=request.supervision_approver_role or None, approval_reference=request.supervision_approval_reference, action=request.supervision_approval_action, rationale=request.supervision_approval_rationale, evidence_ids=request.evidence_ids)
            if not result.continued:
                operation = self._operation(request, DeploymentState.BLOCKED_APPROVAL.value, result.reasons or ("supervised approval is required",))
                return self.result_handler.handle(operation)
        return None

    def _review_control_preflight(self, request: DeploymentRequest) -> DeploymentResult | None:
        """Enforce formal mandatory review and no-go controls when enabled."""
        if not request.review_control_enabled:
            return None
        records: list[MandatoryReviewRecord] = []
        blockers: list[NoGoBlocker] = []
        for raw in request.review_control_checkpoint_records:
            try:
                records.append(MandatoryReviewRecord.model_validate(raw))
            except Exception:
                continue
        for raw in request.review_control_blockers:
            try:
                blockers.append(NoGoBlocker.model_validate(raw))
            except Exception:
                continue
        readiness = self.readiness_gate.assess(stage=request.review_control_stage, checkpoint_records=records, blockers=blockers, proof_status="verified" if request.verification_required is False else "not_verifiable_with_current_inputs", evidence_ids=request.evidence_ids, field_feasibility_status="feasible", production_requested=request.production_requested, approval_present=request.review_control_approval_present, governance_reference=request.review_control_governance_reference)
        if not readiness.production_ready:
            reasons = readiness.reasons or ("mandatory review control did not produce a production-ready outcome",)
            operation = self._operation(request, DeploymentState.BLOCKED_APPROVAL.value if readiness.no_go_evaluation.outcome.value == "pending_review" else DeploymentState.BLOCKED_POLICY.value, tuple(reasons))
            return self.result_handler.handle(operation)
        return None

    def _governance_preflight(self, request: DeploymentRequest) -> DeploymentResult | None:
        """Enforce explicit human checkpoints when the deployment requests governance."""
        if self.governance_policy is None or not request.governance_required:
            return None
        try:
            risk = RiskClass(request.governance_risk_class)
        except ValueError:
            operation = self._operation(request, DeploymentState.BLOCKED_APPROVAL.value, (f"unsupported governance risk class: {request.governance_risk_class}",))
            return self.result_handler.handle(operation)
        requirement = self.accountability_matrix.resolve(workflow=request.governance_workflow, decision_class=DecisionClass.DEPLOYMENT, risk_class=risk)
        checkpoints: list[CheckpointRecord] = []
        for index, raw in enumerate(getattr(request, "governance_checkpoints", ())):
            try:
                checkpoints.append(CheckpointRecord.model_validate(raw))
            except Exception:
                continue
        for index, reference in enumerate(request.reviewer_references):
            checkpoints.append(CheckpointRecord(checkpoint_id=f"{request.deployment_id}:review:{index}", workflow=request.governance_workflow, checkpoint_type=CheckpointType.REVIEW, principal_id=f"reviewer:{index}", role=requirement.required_reviewer_roles[index] if index < len(requirement.required_reviewer_roles) else "technical_reviewer", outcome="accepted", rationale="explicit reviewer reference supplied", reference=reference, evidence_ids=request.evidence_ids))
        for index, reference in enumerate(request.signoff_references):
            checkpoints.append(CheckpointRecord(checkpoint_id=f"{request.deployment_id}:approval:{index}", workflow=request.governance_workflow, checkpoint_type=CheckpointType.APPROVAL, principal_id=f"approver:{index}", role=requirement.required_approver_roles[index] if index < len(requirement.required_approver_roles) else "deployment_approver", outcome="accepted", rationale="explicit approval reference supplied", reference=reference, evidence_ids=request.evidence_ids))
        if request.accountable_owner_reference:
            checkpoints.append(CheckpointRecord(checkpoint_id=f"{request.deployment_id}:accountability", workflow=request.governance_workflow, checkpoint_type=CheckpointType.ACCOUNTABILITY, principal_id="accountable_owner", role=requirement.accountable_owner_role, outcome="accepted", rationale="accountable owner reference supplied", reference=request.accountable_owner_reference, evidence_ids=request.evidence_ids))
        if request.execution_authority_reference:
            checkpoints.append(CheckpointRecord(checkpoint_id=f"{request.deployment_id}:execution", workflow=request.governance_workflow, checkpoint_type=CheckpointType.EXECUTION_AUTHORITY, principal_id="execution_authority", role=requirement.execution_authority_roles[0] if requirement.execution_authority_roles else "deployment_operator", outcome="accepted", rationale="execution authority reference supplied", reference=request.execution_authority_reference, evidence_ids=request.evidence_ids))
        evaluation = self.governance_policy.evaluate(requirement, checkpoints)
        sod = self.separation_policy.evaluate(workflow=requirement.workflow, risk_class=risk, checkpoints=checkpoints)
        if evaluation.allowed and sod.allowed:
            if self.audit_trail is not None:
                self.audit_trail.record("governance.signoff", request.actor or "deployment_orchestrator", {"deployment_id": request.deployment_id, "workflow": requirement.workflow, "state": evaluation.state, "pending_checkpoints": list(evaluation.pending_checkpoints), "separation_allowed": sod.allowed, "evidence_ids": list(evaluation.evidence_ids)}, outcome="allowed")
            return None
        reasons = evaluation.reasons + sod.reasons
        operation = self._operation(request, DeploymentState.BLOCKED_APPROVAL.value, tuple(dict.fromkeys(reasons)))
        if self.audit_trail is not None:
            self.audit_trail.record("governance.signoff", request.actor or "deployment_orchestrator", {"deployment_id": request.deployment_id, "workflow": requirement.workflow, "state": evaluation.state, "pending_checkpoints": list(evaluation.pending_checkpoints), "separation_allowed": sod.allowed, "evidence_ids": list(evaluation.evidence_ids)}, outcome="blocked")
        return self.result_handler.handle(operation)

    def _safety(self, request: DeploymentRequest) -> SafetyAssessment:
        """Classify dry-run as read-only and real deployment as disruptive."""
        if request.dry_run:
            return self.safety_classifier.classify(request.deployment_id, "collect_evidence", production_requested=False, human_change_approval=request.approved, evidence_ids=request.evidence_ids)
        return self.safety_classifier.classify(request.deployment_id, "replace_config", remote=True, destructive=request.remote_destructive, rollback_artifact_available=bool(request.rollback_reference), production_requested=request.production_requested, human_change_approval=request.approved, evidence_ids=request.evidence_ids)

    def _prepare_backup(self, request: DeploymentRequest, backup_provider: BackupProvider | None) -> tuple[DeploymentRequest, DeploymentResult | None]:
        """Require or create a backup reference before real execution."""
        if request.backup_reference:
            return request, None
        if backup_provider is None:
            operation = self._operation(request, DeploymentState.BLOCKED_BACKUP.value, ("mandatory backup reference is missing",))
            return request, self.result_handler.handle(operation)
        try:
            reference = str(backup_provider(request))
        except Exception:
            reference = ""
        if not reference or reference.startswith("secret://"):
            operation = self._operation(request, DeploymentState.BLOCKED_BACKUP.value, ("backup provider did not return a non-secret backup reference",))
            return request, self.result_handler.handle(operation)
        return replace(request, backup_reference=reference), None

    def _operation(self, request: DeploymentRequest, state: str, reasons: tuple[str, ...]) -> DeploymentOperation:
        """Create a safe blocked operation without opening a transport."""
        return DeploymentOperation(f"{request.deployment_id}:blocked", request.deployment_id, request.transport, request.device_id, state, request.dry_run, False, hashlib.sha256(request.rendered_config.encode("utf-8")).hexdigest(), reasons=tuple(dict.fromkeys(reasons)), evidence_ids=request.evidence_ids, rollback_available=bool(request.rollback_reference))

    def _audit(self, request: DeploymentRequest, result: DeploymentResult) -> None:
        """Record secret-safe deployment attempt metadata."""
        if self.audit_trail is None:
            return
        details = {"deployment_id": request.deployment_id, "change_id": request.change_id, "device_id": request.device_id, "vendor": request.vendor, "platform": request.platform, "transport": request.transport, "dry_run": request.dry_run, "state": result.state, "gate": result.gate, "evidence_ids": list(result.evidence_ids), "override_ids": list(request.override_ids), "decision_provenance": list(request.decision_provenance), "review_control_enabled": request.review_control_enabled, "review_control_stage": request.review_control_stage}
        self.audit_trail.record_deployment_attempt(request.actor or "deployment_orchestrator", details, outcome=result.state)

    def _audit_rollback(self, request: DeploymentRequest, assessment: RollbackAssessment) -> None:
        """Record rollback assessment metadata without commands or secrets."""
        if self.audit_trail is None:
            return
        self.audit_trail.record_rollback_attempt(request.actor or "deployment_orchestrator", {"deployment_id": request.deployment_id, "change_id": request.change_id, "rollback_decision": assessment.decision, "scope": list(assessment.scope), "evidence_ids": list(assessment.evidence_ids)}, outcome=assessment.decision)
