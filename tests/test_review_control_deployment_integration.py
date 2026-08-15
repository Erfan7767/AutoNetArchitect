from deployment import DeploymentOrchestrator, DeploymentRequest, DeploymentState

def test_deployment_blocks_when_review_control_is_enabled_without_checkpoint():
    request = DeploymentRequest(deployment_id="D-RC-1", change_id="C-1", device_id="edge-1", vendor="cisco", platform="ios_xe", transport="ssh", rendered_config="interface Gi1", endpoint_reference="oob://edge-1", credential_reference="secret://vault/edge-1", approved=True, backup_reference="backup://D-RC-1", rollback_reference="rollback://D-RC-1", dry_run=False, production_requested=True, verification_required=False, review_control_enabled=True, review_control_approval_present=True)
    result = DeploymentOrchestrator().deploy(request, driver=lambda payload: {"status": "success"})
    assert result.state in {DeploymentState.BLOCKED_POLICY.value, DeploymentState.BLOCKED_APPROVAL.value}

def test_deployment_can_continue_after_formal_pre_go_no_go_checkpoint():
    record = {"checkpoint_id": "deployment.pre_go_no_go", "workflow_stage": "deployment", "status": "resolved", "reviewer_id": "approver", "reviewer_role": "deployment_approver", "decision_reference": "approval://deploy/2", "rationale": "backup rollback and verification reviewed", "evidence_ids": ["backup-1", "rollback-1", "verify-1"]}
    request = DeploymentRequest(deployment_id="D-RC-2", change_id="C-2", device_id="edge-1", vendor="cisco", platform="ios_xe", transport="ssh", rendered_config="interface Gi1", endpoint_reference="oob://edge-1", credential_reference="secret://vault/edge-1", approved=True, backup_reference="backup://D-RC-2", rollback_reference="rollback://D-RC-2", dry_run=False, production_requested=True, verification_required=False, review_control_enabled=True, review_control_checkpoint_records=(record,), review_control_approval_present=True)
    result = DeploymentOrchestrator().deploy(request, driver=lambda payload: {"status": "success"})
    assert result.state != DeploymentState.BLOCKED_POLICY.value and result.state != DeploymentState.BLOCKED_APPROVAL.value
