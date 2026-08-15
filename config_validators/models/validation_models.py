"""Typed validation diagnostics and aggregate report models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .validation_enums import CoverageStatus, Severity, ValidationStage, ValidationStatus


@dataclass(frozen=True)
class ValidationDiagnostic:
    """One traceable validation diagnostic."""

    code: str
    message: str
    severity: Severity
    stage: ValidationStage
    line_number: int | None = None
    command: str | None = None
    referenced_name: str | None = None
    referenced_from: str | None = None
    expected_definition_location: str | None = None
    remediation: str | None = None
    coverage_status: CoverageStatus = CoverageStatus.VALIDATED
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationLineResult:
    """Per-line syntax result."""

    line_number: int
    line: str
    valid: bool
    coverage_status: CoverageStatus
    diagnostics: tuple[ValidationDiagnostic, ...] = ()
    mode_after: str = "global"


@dataclass(frozen=True)
class ValidationBlockResult:
    """Structural block result."""

    valid: bool
    block_type: str
    diagnostics: tuple[ValidationDiagnostic, ...] = ()
    children: tuple["ValidationBlockResult", ...] = ()


@dataclass(frozen=True)
class CoverageRecord:
    """Coverage facts for one vendor/platform."""

    vendor: str
    platform: str
    total_known_commands: int
    validated_commands: int
    partially_covered: tuple[str, ...] = ()
    uncovered_commands: tuple[str, ...] = ()

    @property
    def coverage_percentage(self) -> float:
        """Return syntax-and-semantics coverage percentage."""
        if self.total_known_commands <= 0:
            return 0.0
        return round(self.validated_commands * 100.0 / self.total_known_commands, 2)


@dataclass(frozen=True)
class ValidationReport:
    """Complete offline validation result and pre-deployment gate status."""

    overall_status: ValidationStatus
    vendor: str
    platform: str
    device_model: str | None
    platform_version: str | None
    errors: tuple[ValidationDiagnostic, ...] = ()
    warnings: tuple[ValidationDiagnostic, ...] = ()
    info: tuple[ValidationDiagnostic, ...] = ()
    coverage_percentage: float = 0.0
    uncovered_sections: tuple[str, ...] = ()
    validation_duration_ms: int = 0
    stage_results: dict[str, bool] = field(default_factory=dict)
    deployment_gate: str = "blocked"

    @property
    def can_deploy(self) -> bool:
        """Return true only for a clean passed report with no errors."""
        return self.overall_status is ValidationStatus.PASSED and not self.errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize the report for audit and deployment orchestrators."""
        return {
            "overall_status": self.overall_status.value,
            "vendor": self.vendor,
            "platform": self.platform,
            "device_model": self.device_model,
            "platform_version": self.platform_version,
            "errors": [diagnostic.__dict__ | {"severity": diagnostic.severity.value, "stage": diagnostic.stage.value, "coverage_status": diagnostic.coverage_status.value} for diagnostic in self.errors],
            "warnings": [diagnostic.__dict__ | {"severity": diagnostic.severity.value, "stage": diagnostic.stage.value, "coverage_status": diagnostic.coverage_status.value} for diagnostic in self.warnings],
            "info": [diagnostic.__dict__ | {"severity": diagnostic.severity.value, "stage": diagnostic.stage.value, "coverage_status": diagnostic.coverage_status.value} for diagnostic in self.info],
            "coverage_percentage": self.coverage_percentage,
            "uncovered_sections": list(self.uncovered_sections),
            "validation_duration_ms": self.validation_duration_ms,
            "stage_results": dict(self.stage_results),
            "deployment_gate": self.deployment_gate,
        }
