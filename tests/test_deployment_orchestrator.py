from dataclasses import dataclass
import tempfile

from audit.audit_trail import AuditTrail
from deployment import DeploymentOrchestrator, DeploymentRequest, DeploymentState, RollbackRequest


@dataclass(frozen=True)
class VerificationStub:
    proof_status: str
    production_suitable: bool
    evidence_basis: tuple[str, ...] = ()


def _request(**overrides):
    values = {"deployment_id": "DEP-1", "change_id": "CHG-1", "device_id": "edge-1", "vendor": "cisco", "platform": "ios_xe", "transport": "ssh", "rendered_config": "interface Gi1", "endpoint_reference": "oob://edge-1", "credential_reference": "secret://vault/edge-1", "approved": True, "backup_reference": "backup://DEP-1", "rollback_reference": "rollback://DEP-1", "production_requested": True, "dry_run": False, "actor": "alice"}
    values.update(overrides)
    return DeploymentRequest(**values)


def test_deployment_orchestrator_dry_run_is_review_only():
    request = _request(dry_run=True, production_requested=False)
    result = DeploymentOrchestrator().deploy(request)
    assert result.state == DeploymentState.DRY_RUN.value
    assert result.gate == "review_only"
    assert result.operation is not None
    assert result.operation.dry_run is True


def test_deployment_orchestrator_blocks_approval_and_human_data_gates():
    blocked_approval = DeploymentOrchestrator().deploy(_request(approved=False))
    assert blocked_approval.state == DeploymentState.BLOCKED_APPROVAL.value
    blocked_state = DeploymentOrchestrator().deploy(_request(project_valid=False))
    assert blocked_state.state == DeploymentState.BLOCKED_INVALID_PROJECT_STATE.value
    blocked_human = DeploymentOrchestrator().deploy(_request(unresolved_human_inputs=("oob_endpoint",)))
    assert blocked_human.state == DeploymentState.BLOCKED_HUMAN_DATA.value


def test_deployment_orchestrator_requires_backup_and_verifies_real_deploy():
    missing_backup = DeploymentOrchestrator().deploy(_request(backup_reference=""), driver=lambda payload: {"status": "success"})
    assert missing_backup.state == DeploymentState.BLOCKED_BACKUP.value
    audit_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    audit_file.close()
    audit = AuditTrail(audit_file.name)
    orchestrator = DeploymentOrchestrator(audit_trail=audit)
    result = orchestrator.deploy(_request(), driver=lambda payload: {"status": "success", "output": "committed", "evidence_ids": ["exec-1"]}, verification_report=VerificationStub("verified", True, ("verify-1",)))
    assert result.state == DeploymentState.VERIFIED.value
    assert result.gate == "allow"
    assert len(audit.query(event_type="deployment.attempt")) == 1


def test_deployment_orchestrator_records_rollback_review_after_failed_driver():
    rollback_request = RollbackRequest("RB-1", ("edge-1",), ("baseline-1",), ("current-1",), {key: True for key in ("management_access", "authentication", "audit_logging", "segmentation", "rollback_artifact_retained")}, validation_evidence_ids=("rb-val-1",))
    result = DeploymentOrchestrator().deploy(_request(), driver=lambda payload: {"status": "failed", "output": "failure"}, rollback_request=rollback_request)
    assert result.state == DeploymentState.ROLLBACK_REVIEW.value


from pathlib import Path
from orchestrators import DeploymentOrchestrator as LifecycleDeploymentOrchestrator
from orchestrators import DesignOrchestrator as LifecycleDesignOrchestrator
from orchestrators import MasterOrchestrator as LifecycleMasterOrchestrator
from orchestrators import WorkflowStage as LifecycleWorkflowStage
from source_of_truth.sot_manager import SoTManager


def _lifecycle_prepared(tmp_path: Path, approval_refs: tuple[str, ...] = ("deployment_approval",)):
    audit = AuditTrail(tmp_path / "lifecycle-audit.jsonl")
    master = LifecycleMasterOrchestrator(sot_manager=SoTManager(tmp_path / "lifecycle-sot.json"), audit_trail=audit)
    context = master.create_context(project_id="lifecycle-project", actor="operator", completed_through=LifecycleWorkflowStage.CONFIG_GENERATION, evidence_ids=("e1",), approval_references=approval_refs)
    master.register_transition_sot(context, sot_type="DESIGN", payload={"artifact_ids": ["design-artifact"]}, source="design-service", authority="architect", evidence_ids=("design-e1",), approval_reference="design-approval")
    deployment = LifecycleDeploymentOrchestrator(master=master)
    prepare_result = deployment.prepare(context, {"deployment_artifact_id": "deployment-package"}, evidence_ids=("deploy-e1",), approval_reference="deployment-approval")
    assert prepare_result.success is True
    return master, deployment, context, audit


def test_lifecycle_prepare_requires_design_sot():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = AuditTrail(root / "audit.jsonl")
        master = LifecycleMasterOrchestrator(sot_manager=SoTManager(root / "sot.json"), audit_trail=audit)
        context = master.create_context(project_id="deployment-project-2", actor="operator", completed_through=LifecycleWorkflowStage.REQUIREMENTS)
        deployment = LifecycleDeploymentOrchestrator(master=master)
        result = deployment.prepare(context, {"deployment_artifact_id": "package"})
        assert result.success is False
        assert "SoT" in " ".join(result.reasons)


def test_lifecycle_real_deployment_requires_backup_and_approval():
    with tempfile.TemporaryDirectory() as tmp:
        _master_value, deployment, context, _audit = _lifecycle_prepared(Path(tmp), approval_refs=())
        result = deployment.execute(context, {"execution_result_id": "exec-1"}, real_execution=True)
        assert result.success is False
        reasons = " ".join(result.reasons)
        assert "approval" in reasons
        assert "backup" in reasons
        assert context.current_stage == LifecycleWorkflowStage.DEPLOYMENT_PREPARATION.value


def test_lifecycle_real_deployment_succeeds_only_with_explicit_gates():
    with tempfile.TemporaryDirectory() as tmp:
        _master_value, deployment, context, audit = _lifecycle_prepared(Path(tmp))
        result = deployment.execute(context, {"execution_result_id": "exec-2", "backup_reference": "backup://lifecycle-project/2026-08-14", "destructive_operation_approval": True, "state": "executed"}, evidence_ids=("execution-e1",), real_execution=True)
        assert result.success is True
        assert result.data["execution_mode"] == "real"
        assert context.current_stage == LifecycleWorkflowStage.DEPLOYMENT_EXECUTION.value
        assert audit.query(event_type="orchestrator.stage_transition")


def test_lifecycle_remote_destructive_path_is_blocked_without_specific_approval():
    with tempfile.TemporaryDirectory() as tmp:
        _master_value, deployment, context, _audit = _lifecycle_prepared(Path(tmp))
        result = deployment.execute(context, {"execution_result_id": "exec-3", "backup_reference": "backup://ref", "remote_destructive": True}, real_execution=True)
        assert result.success is False
        assert "remote-destructive" in " ".join(result.reasons)
