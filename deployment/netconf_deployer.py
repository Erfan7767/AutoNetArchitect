"""NETCONF deployment adapter with candidate-safe execution boundaries."""

from __future__ import annotations

from .deployer_common import BaseDeployer, BackupProvider, DeploymentDriver
from .deployment_models import DeploymentOperation, DeploymentRequest


class NETCONFDeployer(BaseDeployer):
    """Deploy configuration through an explicitly supplied NETCONF driver."""

    protocol = "netconf"
    supported_vendors = ("aruba", "cisco", "huawei", "juniper")

    def deploy(self, request: DeploymentRequest, *, driver: DeploymentDriver | None = None, backup_provider: BackupProvider | None = None) -> DeploymentOperation:
        """Execute dry-run or invoke the caller-owned NETCONF driver."""
        if request.transport.lower() != self.protocol:
            return self._transport_mismatch(request)
        return super().deploy(request, driver=driver, backup_provider=backup_provider)

    @staticmethod
    def _transport_mismatch(request: DeploymentRequest) -> DeploymentOperation:
        """Return a safe mismatch operation."""
        import hashlib
        config_hash = hashlib.sha256(request.rendered_config.encode("utf-8")).hexdigest()
        return DeploymentOperation(f"{request.deployment_id}:transport-mismatch", request.deployment_id, "netconf", request.device_id, "blocked_policy", request.dry_run, False, config_hash, reasons=("request transport does not match netconf deployer",), evidence_ids=request.evidence_ids)
