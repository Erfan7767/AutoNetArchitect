from dataclasses import dataclass

from deployment.deployment_models import DeploymentOperation, DeploymentState
from deployment.deployment_result_handler import DeploymentResultHandler
from deployment.rollback_manager import RollbackAssessment


@dataclass(frozen=True)
class VerificationStub:
    proof_status: str
    production_suitable: bool
    evidence_basis: tuple[str, ...] = ()


def _operation(state=DeploymentState.EXECUTED.value):
    return DeploymentOperation("OP-1", "DEP-1", "ssh", "edge-1", state, False, state == DeploymentState.EXECUTED.value, "hash-1", evidence_ids=("exec-1",), rollback_available=True)


def test_handler_requires_verification_after_execution():
    result = DeploymentResultHandler().handle(_operation())
    assert result.state == DeploymentState.VERIFICATION_PENDING.value
    assert result.gate == "block_or_review"
    assert "post_deploy_verification_report" in result.required_human_inputs


def test_handler_allows_only_verified_production_suitable_result():
    result = DeploymentResultHandler().handle(_operation(), verification=VerificationStub("verified", True, ("verify-1",)))
    assert result.state == DeploymentState.VERIFIED.value
    assert result.gate == "allow"
    assert result.evidence_ids == ("exec-1", "verify-1")


def test_handler_failed_verification_with_reviewable_rollback_is_rollback_review():
    rollback = RollbackAssessment("RB-1", "ready_for_review", ("edge-1",), False, {"management_access": True, "authentication": True, "audit_logging": True, "segmentation": True, "rollback_artifact_retained": True}, ("confirm target identity",), (), ("rollback evidence",), ("rb-1",))
    result = DeploymentResultHandler().handle(_operation(), verification=VerificationStub("failed", False, ("verify-fail",)), rollback=rollback)
    assert result.state == DeploymentState.ROLLBACK_REVIEW.value
    assert result.gate == "block_or_review"
    assert "rb-1" in result.evidence_ids


def test_handler_dry_run_is_review_only_and_blocked_operation_is_blocked():
    dry_run = DeploymentResultHandler().handle(_operation(DeploymentState.DRY_RUN.value))
    assert dry_run.gate == "review_only"
    blocked = DeploymentResultHandler().handle(_operation(DeploymentState.BLOCKED_BACKUP.value))
    assert blocked.gate == "blocked"
    assert "backup_reference" in blocked.required_human_inputs
