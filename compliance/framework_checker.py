"""Shared checker adapter for framework-specific technical assessments."""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .compliance_engine import ComplianceEngine
from .compliance_models import ComplianceAssessment, ComplianceFramework, ComplianceScope, EvidenceReference
from .scope_definitions import default_scope


class FrameworkChecker:
    """Delegate one framework assessment to the governed engine."""

    framework: ComplianceFramework
    framework_name: str

    def __init__(self, engine: ComplianceEngine | None = None) -> None:
        """Initialize an optional shared engine."""
        self.engine = engine or ComplianceEngine()

    def assess(self, *, evidence: Sequence[EvidenceReference] = (), control_observations: Mapping[str, Mapping[str, Any]] | None = None, scope: ComplianceScope | None = None, framework_version: str | None = None, organization_scope: str | None = None, system_scope: str | None = None, authoritative_obligations_supplied: bool = False, sot_basis: Mapping[str, str] | None = None, actor: str = "compliance-checker") -> ComplianceAssessment:
        """Run a technical-only assessment for the checker framework."""
        selected_scope = scope or default_scope(self.framework, framework_version=framework_version, organization_scope=organization_scope, system_scope=system_scope, authoritative_obligations_supplied=authoritative_obligations_supplied)
        if selected_scope.framework != self.framework:
            raise ValueError(f"scope framework {selected_scope.framework.value} does not match {self.framework.value}")
        return self.engine.assess(framework=self.framework, scope=selected_scope, evidence=evidence, control_observations=control_observations, sot_basis=sot_basis, actor=actor)
