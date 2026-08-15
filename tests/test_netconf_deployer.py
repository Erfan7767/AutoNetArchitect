from deployment.deployment_models import DeploymentRequest, DeploymentState
from deployment.netconf_deployer import NETCONFDeployer


def _request(**overrides):
    values = {"deployment_id": "NC-1", "change_id": "CHG-NC", "device_id": "core-1", "vendor": "juniper", "platform": "junos", "transport": "netconf", "rendered_config": "set system host-name core-1", "endpoint_reference": "oob://core-1", "credential_reference": "secret://vault/core-1", "approved": True, "backup_reference": "backup://NC-1", "rollback_reference": "rollback://NC-1", "production_requested": True, "dry_run": False, "actor": "tester"}
    values.update(overrides)
    return DeploymentRequest(**values)


def test_netconf_dry_run_is_non_executing():
    operation = NETCONFDeployer().deploy(_request(dry_run=True, production_requested=False), driver=lambda payload: {"status": "success"})
    assert operation.state == DeploymentState.DRY_RUN.value
    assert operation.protocol == "netconf"
    assert operation.dry_run is True


def test_netconf_real_driver_success_is_executed():
    operation = NETCONFDeployer().deploy(_request(), driver=lambda payload: {"status": "ok", "provider_reference": "nc-session-1"})
    assert operation.state == DeploymentState.EXECUTED.value
    assert operation.provider_reference == "nc-session-1"
    assert operation.rollback_available is True


def test_netconf_requires_backup_and_rejects_transport_mismatch():
    missing_backup = NETCONFDeployer().deploy(_request(backup_reference=""), driver=lambda payload: {"status": "success"})
    assert missing_backup.state == DeploymentState.BLOCKED_BACKUP.value
    mismatch = NETCONFDeployer().deploy(_request(transport="ssh"), driver=lambda payload: {"status": "success"})
    assert mismatch.state == DeploymentState.BLOCKED_POLICY.value
