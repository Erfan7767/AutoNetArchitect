"""Chaos test for SSH transport timeout handling."""
from __future__ import annotations

from deployment.deployment_models import DeploymentRequest, DeploymentState
from deployment.ssh_deployer import SSHDeployer


def test_ssh_timeout_returns_failed_operation_without_raw_exception():
    request = DeploymentRequest(deployment_id="SSH-CHAOS", change_id="CHG-CHAOS", device_id="DEVICE-CHAOS", vendor="cisco", platform="ios-xe", transport="ssh", rendered_config="interface Gi1/0/1", endpoint_reference="oob://device", credential_reference="secret://cred", backup_reference="backup://SSH-CHAOS", rollback_reference="rollback://SSH-CHAOS", dry_run=False, production_requested=True, approved=True, actor="chaos-engineer")

    def timeout_driver(_payload):
        raise TimeoutError("simulated SSH timeout")

    operation = SSHDeployer().deploy(request, driver=timeout_driver)
    assert operation.state == DeploymentState.FAILED.value
    assert operation.rollback_available is True
    assert any("failed" in reason.lower() for reason in operation.reasons)
    assert "simulated SSH timeout" not in operation.output
