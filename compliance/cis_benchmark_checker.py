"""CIS network device benchmark technical checker."""
from __future__ import annotations
from typing import Any
from .framework_checker import FrameworkChecker
from .compliance_models import ComplianceAssessment, ComplianceFramework

class CISBenchmarkComplianceChecker(FrameworkChecker):
    """Assess hardening mappings only when exact benchmark version and device scope are known."""
    framework = ComplianceFramework.CIS_BENCHMARK
    framework_name = "CIS network device benchmark technical assessment"

    def assess(self, *, framework_version: str | None = None, **kwargs: Any) -> ComplianceAssessment:
        """Keep the assessment non-authoritative when the exact benchmark edition is absent."""
        if not framework_version and kwargs.get("scope") is None:
            kwargs["authoritative_obligations_supplied"] = False
        return super().assess(framework_version=framework_version, **kwargs)

CisBenchmarkChecker = CISBenchmarkComplianceChecker
