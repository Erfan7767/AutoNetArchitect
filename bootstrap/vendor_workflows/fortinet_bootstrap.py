"""Fortinet FortiOS bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class FortinetBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for FortiGate and FortiOS families."""

    vendor = "fortinet"
    family_name = "fortios_security_platforms"
    platform_aliases = ("fortios", "fortigate")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return FortiOS-specific intent checkpoints."""
        return super().steps(request) + (BootstrapStep("ha_review", "Review FortiOS HA intent", "confirm HA mode and peer identity from human-supplied design evidence", True, False, ("HA mode evidence reviewed",)),)


FortinetBootstrap = FortinetBootstrapWorkflow
