from deployment import DeploymentOrchestrator, DeploymentRequest, DeploymentState
from supervised_mode.supervision_context import SupervisionContext
from supervised_mode.workflow_mode import WorkflowMode

def test_deployment_orchestrator_requires_supervised_approval_when_context_is_enabled():
    context = SupervisionContext(project_id="p-1", workflow_run_id="run-1", mode=WorkflowMode.SUPERVISED, high_assurance=True, human_owner_id="eng-1")
    request = DeploymentRequest(deployment_id="D-SUP-1", change_id="C-1", device_id="edge-1", vendor="cisco", platform="ios_xe", transport="ssh", rendered_config="interface Gi1", endpoint_reference="oob://edge-1", credential_reference="secret://vault/edge-1", approved=True, backup_reference="backup://D-SUP-1", rollback_reference="rollback://D-SUP-1", dry_run=False, production_requested=True, actor="operator", supervised_mode=True)
    result = DeploymentOrchestrator(supervision_context=context).deploy(request, driver=lambda payload: {"status": "success", "output": "committed"})
    assert result.state == DeploymentState.BLOCKED_APPROVAL.value

def test_deployment_orchestrator_continues_after_supervised_approval():
    context = SupervisionContext(project_id="p-1", workflow_run_id="run-2", mode=WorkflowMode.SUPERVISED, high_assurance=True, human_owner_id="eng-1")
    request = DeploymentRequest(deployment_id="D-SUP-2", change_id="C-2", device_id="edge-1", vendor="cisco", platform="ios_xe", transport="ssh", rendered_config="interface Gi1", endpoint_reference="oob://edge-1", credential_reference="secret://vault/edge-1", approved=True, backup_reference="backup://D-SUP-2", rollback_reference="rollback://D-SUP-2", dry_run=False, production_requested=True, actor="operator", supervised_mode=True, supervision_approver_id="approver-1", supervision_approver_role="deployment_approver", supervision_approval_action="approve", supervision_approval_rationale="backup and rollback verified", supervision_approval_reference="approval://D-SUP-2")
    result = DeploymentOrchestrator(supervision_context=context).deploy(request, driver=lambda payload: {"status": "success", "output": "committed"})
    assert result.state != DeploymentState.BLOCKED_APPROVAL.value
