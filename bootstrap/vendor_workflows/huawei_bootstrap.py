"""Huawei VRP bootstrap workflow intents."""

from __future__ import annotations

from .common import BootstrapRequest, BootstrapStep, VendorBootstrapWorkflow


class HuaweiBootstrapWorkflow(VendorBootstrapWorkflow):
    """Bootstrap intent workflow for Huawei VRP families."""

    vendor = "huawei"
    family_name = "huawei_vrp_platforms"
    platform_aliases = ("vrp", "vrp8")

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return VRP identity and management review intents."""
        return super().steps(request) + (BootstrapStep("vrp_review", "Review Huawei VRP evidence", "confirm VRP release, model capability, and rollback method from validated evidence", True, False, ("VRP release evidence linked", "rollback method reviewed")),)


HuaweiBootstrap = HuaweiBootstrapWorkflow
