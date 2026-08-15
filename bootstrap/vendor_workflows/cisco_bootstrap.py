"""Cisco family bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class CiscoBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for Cisco IOS XE, IOS, NX-OS, ASA, and WLC families."""

    vendor = "cisco"
    family_name = "cisco_network_platforms"
    platform_aliases = ("ios_xe", "ios", "nxos", "asa", "wlc")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return Cisco-family bootstrap intents with platform-neutral syntax."""
        return super().steps(request) + (BootstrapStep("capability_review", "Review Cisco platform capability", "confirm target platform and model support before any command rendering", True, False, ("capability evidence linked",)),)


CiscoBootstrap = CiscoBootstrapWorkflow
