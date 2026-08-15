"""Orchestration of vendor-family bootstrap planning."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from .vendor_workflows import (
    ArubaBootstrapWorkflow,
    BootstrapArtifact,
    BootstrapRequest,
    BootstrapStatus,
    CiscoBootstrapWorkflow,
    FortinetBootstrapWorkflow,
    HuaweiBootstrapWorkflow,
    JuniperBootstrapWorkflow,
    MikroTikBootstrapWorkflow,
    PaloAltoBootstrapWorkflow,
    VendorBootstrapWorkflow,
)


class BootstrapOrchestrator:
    """Select and execute only validated vendor-family bootstrap planners."""

    def __init__(self, preview_only_vendors: Iterable[str] = ()) -> None:
        """Create an orchestrator with optional explicit preview-only vendors."""
        workflows = (CiscoBootstrapWorkflow(), FortinetBootstrapWorkflow(), PaloAltoBootstrapWorkflow(), HuaweiBootstrapWorkflow(), ArubaBootstrapWorkflow(), JuniperBootstrapWorkflow(), MikroTikBootstrapWorkflow())
        self._workflows: dict[str, VendorBootstrapWorkflow] = {}
        for workflow in workflows:
            self._workflows[workflow.vendor] = workflow
            for alias in workflow.platform_aliases:
                self._workflows[alias.lower()] = workflow
        self._preview_only_vendors = {str(vendor).strip().lower() for vendor in preview_only_vendors if str(vendor).strip()}

    def workflow_for(self, vendor: str, platform: str = "") -> VendorBootstrapWorkflow | None:
        """Return a validated workflow by vendor or platform alias."""
        vendor_key = str(vendor).strip().lower()
        return self._workflows.get(vendor_key)

    def build(self, request: BootstrapRequest) -> BootstrapArtifact:
        """Build one safe bootstrap artifact without establishing a device session."""
        vendor_key = str(request.vendor).strip().lower()
        if vendor_key in self._preview_only_vendors:
            return BootstrapArtifact(f"bootstrap:preview:{request.device_id}:{request.platform}", BootstrapStatus.PREVIEW_ONLY.value, request.vendor, request.platform, request.device_id, False, False, required_human_inputs=("validated_vendor_workflow",), assumptions=("vendor is explicitly preview-only and cannot enter production deployment path",), evidence_ids=request.evidence_ids, secret_references=tuple(reference for reference in (request.credential_reference, request.oob_reference) if reference))
        workflow = self.workflow_for(request.vendor, request.platform)
        if workflow is None:
            return BootstrapArtifact(f"bootstrap:unsupported:{request.device_id}:{request.platform}", BootstrapStatus.BLOCKED_UNSUPPORTED_VENDOR.value, request.vendor, request.platform, request.device_id, False, False, required_human_inputs=("supported_vendor_workflow",), assumptions=("unsupported vendor is not auto-selected for production bootstrap",), evidence_ids=request.evidence_ids)
        return workflow.build(request)

    def build_all(self, requests: Iterable[BootstrapRequest]) -> tuple[BootstrapArtifact, ...]:
        """Build multiple artifacts deterministically in request order."""
        return tuple(self.build(request) for request in requests)

    def supported_vendor_families(self) -> tuple[str, ...]:
        """Return supported V1 vendor families."""
        return tuple(sorted({workflow.vendor for workflow in self._workflows.values()}))

    def preview_only_vendors(self) -> tuple[str, ...]:
        """Return explicit preview-only vendors."""
        return tuple(sorted(self._preview_only_vendors))
