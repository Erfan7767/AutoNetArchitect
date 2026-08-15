"""NCA technical network control checker."""
from __future__ import annotations
from typing import Any, Mapping, Sequence
from .framework_checker import FrameworkChecker
from .compliance_models import ComplianceAssessment, ComplianceFramework, ComplianceScope, EvidenceReference

class NCAComplianceChecker(FrameworkChecker):
    """Assess NCA-related network mappings only after the exact edition and scope are supplied."""
    framework = ComplianceFramework.NCA
    framework_name = "NCA technical network assessment"

    def assess(self, *, framework_version: str | None = None, **kwargs: Any) -> ComplianceAssessment:
        """Require human/authoritative edition input before treating mappings as authoritative."""
        if not framework_version and kwargs.get("scope") is None:
            kwargs["authoritative_obligations_supplied"] = False
        return super().assess(framework_version=framework_version, **kwargs)

NcaChecker = NCAComplianceChecker
