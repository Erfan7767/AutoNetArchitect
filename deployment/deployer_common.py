"""Shared safe transport behavior for deployment execution adapters."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Callable, Mapping

from log_redaction.redacting_filter import RedactingFilter

from .deployment_models import DeploymentOperation, DeploymentRequest, DeploymentState


DeploymentDriver = Callable[[Mapping[str, Any]], Mapping[str, Any]]
BackupProvider = Callable[[DeploymentRequest], str]


class BaseDeployer:
    """Transport adapter that never resolves credentials or invents live output."""

    protocol = ""
    supported_vendors: tuple[str, ...] = ()

    def deploy(self, request: DeploymentRequest, *, driver: DeploymentDriver | None = None, backup_provider: BackupProvider | None = None) -> DeploymentOperation:
        """Perform dry-run or invoke an explicitly supplied transport driver."""
        config_hash = hashlib.sha256(request.rendered_config.encode("utf-8")).hexdigest()
        if request.dry_run:
            return DeploymentOperation(f"{request.deployment_id}:dry-run", request.deployment_id, self.protocol, request.device_id, DeploymentState.DRY_RUN.value, True, False, config_hash, output="dry-run only; no remote session opened", evidence_ids=request.evidence_ids, reasons=("dry-run mode selected",), rollback_available=bool(request.rollback_reference))
        missing = self._missing_inputs(request)
        if missing:
            return DeploymentOperation(f"{request.deployment_id}:blocked", request.deployment_id, self.protocol, request.device_id, DeploymentState.BLOCKED_HUMAN_DATA.value, False, False, config_hash, reasons=tuple(missing), evidence_ids=request.evidence_ids, rollback_available=bool(request.rollback_reference))
        backup_reference = request.backup_reference
        if not backup_reference and backup_provider is not None:
            try:
                backup_reference = str(backup_provider(request))
            except Exception:
                backup_reference = ""
        if not backup_reference:
            return DeploymentOperation(f"{request.deployment_id}:backup-blocked", request.deployment_id, self.protocol, request.device_id, DeploymentState.BLOCKED_BACKUP.value, False, False, config_hash, reasons=("mandatory backup was not created or referenced",), evidence_ids=request.evidence_ids, rollback_available=False)
        if driver is None:
            return DeploymentOperation(f"{request.deployment_id}:driver-blocked", request.deployment_id, self.protocol, request.device_id, DeploymentState.BLOCKED_POLICY.value, False, True, config_hash, reasons=("real deployment driver is not configured",), evidence_ids=request.evidence_ids, rollback_available=bool(request.rollback_reference))
        try:
            response = dict(driver(self._safe_payload(request, backup_reference)))
        except Exception:
            return DeploymentOperation(f"{request.deployment_id}:failed", request.deployment_id, self.protocol, request.device_id, DeploymentState.FAILED.value, False, True, config_hash, reasons=("transport driver failed without exposing runtime details",), evidence_ids=request.evidence_ids, rollback_available=bool(request.rollback_reference))
        raw_output = response.get("output", "")
        sanitized = RedactingFilter.sanitize_value(raw_output)
        output = sanitized if isinstance(sanitized, str) else str(sanitized)
        successful = str(response.get("state", response.get("status", ""))).lower() in {"success", "successful", "executed", "ok"}
        state = DeploymentState.EXECUTED.value if successful else DeploymentState.FAILED.value
        reasons = tuple(str(item) for item in response.get("reasons", ()))
        evidence = tuple(dict.fromkeys(request.evidence_ids + tuple(str(item) for item in response.get("evidence_ids", ()))))
        return DeploymentOperation(f"{request.deployment_id}:operation", request.deployment_id, self.protocol, request.device_id, state, False, bool(backup_reference), config_hash, output=output, provider_reference=str(response.get("provider_reference", "")), evidence_ids=evidence, reasons=reasons, rollback_available=bool(request.rollback_reference))

    def _missing_inputs(self, request: DeploymentRequest) -> tuple[str, ...]:
        """Return human inputs required before a real transport session."""
        missing = [field for field in ("deployment_id", "change_id", "device_id", "vendor", "platform", "transport", "endpoint_reference", "actor") if not getattr(request, field)]
        if request.credential_reference and not request.credential_reference.startswith("secret://"):
            missing.append("credential_reference_must_be_secret_reference")
        if not request.credential_reference and not request.secret_references:
            missing.append("credential_reference")
        if request.vendor.lower() not in self.supported_vendors:
            missing.append("supported_vendor")
        return tuple(dict.fromkeys(missing))

    @staticmethod
    def _safe_payload(request: DeploymentRequest, backup_reference: str) -> dict[str, Any]:
        """Build driver payload containing references and rendered config only."""
        return {"deployment_id": request.deployment_id, "change_id": request.change_id, "device_id": request.device_id, "vendor": request.vendor, "platform": request.platform, "transport": request.transport, "endpoint_reference": request.endpoint_reference, "credential_reference": request.credential_reference, "secret_references": list(request.secret_references), "rendered_config": request.rendered_config, "backup_reference": backup_reference, "rollback_reference": request.rollback_reference, "evidence_ids": list(request.evidence_ids)}
