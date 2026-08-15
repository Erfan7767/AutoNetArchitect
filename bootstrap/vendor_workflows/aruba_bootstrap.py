"""Aruba AOS-CX bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class ArubaBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for Aruba AOS-CX platforms."""

    vendor = "aruba"
    family_name = "aruba_aoscx_platforms"
    platform_aliases = ("aoscx", "arubaos-cx")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return AOS-CX identity and access review intents."""
        return super().steps(request) + (BootstrapStep("access_review", "Review Aruba access baseline", "confirm access role, management source restrictions, and device identity evidence", True, False, ("role evidence linked", "management source evidence linked")),)


ArubaBootstrap = ArubaBootstrapWorkflow
