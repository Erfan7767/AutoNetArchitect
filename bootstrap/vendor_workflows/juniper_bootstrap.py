"""Juniper Junos bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class JuniperBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for Junos platforms."""

    vendor = "juniper"
    family_name = "juniper_junos_platforms"
    platform_aliases = ("junos", "junos-evo")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return Junos commit and rollback review intents."""
        return super().steps(request) + (BootstrapStep("commit_review", "Review Junos commit safety", "confirm candidate configuration, commit safety, and rollback evidence before rendering", True, False, ("candidate diff reviewed", "rollback evidence linked")),)


JuniperBootstrap = JuniperBootstrapWorkflow
