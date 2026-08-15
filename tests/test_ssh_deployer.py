from deployment.deployment_models import DeploymentRequest, DeploymentState
from deployment.ssh_deployer import SSHDeployer


def _request(**overrides):
    values = {"deployment_id": "SSH-1", "change_id": "CHG-SSH", "device_id": "edge-1", "vendor": "cisco", "platform": "ios_xe", "transport": "ssh", "rendered_config": "hostname edge-1", "endpoint_reference": "oob://edge-1", "credential_reference": "secret://vault/edge-1", "approved": True, "backup_reference": "backup://SSH-1", "rollback_reference": "rollback://SSH-1", "production_requested": True, "dry_run": False, "actor": "tester"}
    values.update(overrides)
    return DeploymentRequest(**values)


def test_ssh_dry_run_does_not_call_driver():
    calls = []
    operation = SSHDeployer().deploy(_request(dry_run=True, production_requested=False), driver=lambda payload: calls.append(payload))
    assert operation.state == DeploymentState.DRY_RUN.value
    assert operation.backup_created is False
    assert calls == []


def test_ssh_real_deploy_requires_backup_and_connection_references():
    missing_backup = SSHDeployer().deploy(_request(backup_reference=""), driver=lambda payload: {"status": "success"})
    assert missing_backup.state == DeploymentState.BLOCKED_BACKUP.value
    missing_endpoint = SSHDeployer().deploy(_request(endpoint_reference=""), driver=lambda payload: {"status": "success"})
    assert missing_endpoint.state == DeploymentState.BLOCKED_HUMAN_DATA.value


def test_ssh_real_deploy_sanitizes_driver_output_and_keeps_secret_reference():
    operation = SSHDeployer().deploy(_request(), driver=lambda payload: {"status": "success", "output": "password=secret-value secret://vault/edge-1", "evidence_ids": ["ssh-proof"]})
    assert operation.state == DeploymentState.EXECUTED.value
    assert operation.backup_created is True
    assert "secret-value" not in operation.output
    assert "secret://vault/edge-1" in operation.output
    assert "ssh-proof" in operation.evidence_ids


def test_ssh_unknown_vendor_is_blocked_without_driver_call():
    calls = []
    operation = SSHDeployer().deploy(_request(vendor="unknown_vendor"), driver=lambda payload: calls.append(payload))
    assert operation.state == DeploymentState.BLOCKED_HUMAN_DATA.value
    assert calls == []
