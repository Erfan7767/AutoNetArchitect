from deployment import DeploymentOrchestrator, DeploymentRequest, DeploymentState
from governance.signoff_policy import SignoffPolicy

def _request(**overrides):
    values = {"deployment_id": "DEP-GOV", "change_id": "CHG-GOV", "device_id": "edge-1", "vendor": "cisco", "platform": "ios_xe", "transport": "ssh", "rendered_config": "interface Gi1", "endpoint_reference": "oob://edge-1", "credential_reference": "secret://vault/edge-1", "approved": True, "backup_reference": "backup://DEP-GOV", "rollback_reference": "rollback://DEP-GOV", "production_requested": True, "dry_run": False, "actor": "operator", "governance_required": True, "reviewer_references": ("review://technical", "review://security"), "signoff_references": ("approval://deployment", "approval://service-owner"), "accountable_owner_reference": "owner://deployment", "execution_authority_reference": "approval://execution"}
    values.update(overrides)
    return DeploymentRequest(**values)

def test_deployment_governance_gate_blocks_without_signoffs():
    result = DeploymentOrchestrator(governance_policy=SignoffPolicy()).deploy(_request(reviewer_references=(), signoff_references=(), accountable_owner_reference="", execution_authority_reference=""))
    assert result.state == DeploymentState.BLOCKED_APPROVAL.value

def test_deployment_governance_gate_allows_only_with_explicit_signoffs():
    result = DeploymentOrchestrator(governance_policy=SignoffPolicy()).deploy(_request(), driver=lambda payload: {"status": "success", "output": "committed"}, verification_report=None)
    assert result.state != DeploymentState.BLOCKED_APPROVAL.value
