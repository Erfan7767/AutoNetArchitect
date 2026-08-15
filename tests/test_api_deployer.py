from deployment.api_deployer import APIDeployer
from deployment.deployment_models import DeploymentRequest, DeploymentState


def _request(**overrides):
    values = {"deployment_id": "API-1", "change_id": "CHG-API", "device_id": "fw-1", "vendor": "fortinet", "platform": "fortigate", "transport": "api", "rendered_config": "{\"policy\": []}", "endpoint_reference": "api://fw-1", "credential_reference": "secret://vault/fw-1", "approved": True, "backup_reference": "backup://API-1", "rollback_reference": "rollback://API-1", "production_requested": True, "dry_run": False, "actor": "tester"}
    values.update(overrides)
    return DeploymentRequest(**values)


def test_api_dry_run_requires_no_driver_or_secret_resolution():
    operation = APIDeployer().deploy(_request(dry_run=True, production_requested=False), driver=lambda payload: {"status": "success"})
    assert operation.state == DeploymentState.DRY_RUN.value
    assert operation.backup_created is False


def test_api_real_deploy_passes_reference_only_payload_to_driver():
    observed = []
    operation = APIDeployer().deploy(_request(), driver=lambda payload: observed.append(payload) or {"status": "success", "output": {"result": "accepted"}})
    assert operation.state == DeploymentState.EXECUTED.value
    assert operation.backup_created is True
    assert len(observed) == 1
    assert observed[0]["credential_reference"] == "secret://vault/fw-1"
    assert "credential" not in observed[0] or observed[0]["credential"] == "secret://vault/fw-1"


def test_api_rejects_mismatch_and_missing_backup():
    mismatch = APIDeployer().deploy(_request(transport="ssh"), driver=lambda payload: {"status": "success"})
    assert mismatch.state == DeploymentState.BLOCKED_POLICY.value
    missing_backup = APIDeployer().deploy(_request(backup_reference=""), driver=lambda payload: {"status": "success"})
    assert missing_backup.state == DeploymentState.BLOCKED_BACKUP.value
