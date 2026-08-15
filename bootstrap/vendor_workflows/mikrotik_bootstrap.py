"""MikroTik RouterOS bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class MikroTikBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for MikroTik RouterOS platforms."""

    vendor = "mikrotik"
    family_name = "mikrotik_routeros_platforms"
    platform_aliases = ("routeros", "ros")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return RouterOS management and safe-save review intents."""
        return super().steps(request) + (BootstrapStep("safe_save_review", "Review RouterOS safe-save method", "confirm safe configuration save and recovery access from human-supplied evidence", True, False, ("safe-save evidence linked", "recovery access verified")),)


MikroTikBootstrap = MikroTikBootstrapWorkflow
