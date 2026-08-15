"""Palo Alto PAN-OS bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class PaloAltoBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for Palo Alto Networks PAN-OS platforms."""

    vendor = "paloalto"
    family_name = "panos_security_platforms"
    platform_aliases = ("panos", "paloalto")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return PAN-OS management and policy-review intents."""
        return super().steps(request) + (BootstrapStep("policy_review", "Review PAN-OS policy safety", "confirm management plane and security policy ownership before rendering commands", True, False, ("policy ownership evidence linked",)),)


PaloAltoBootstrap = PaloAltoBootstrapWorkflow
