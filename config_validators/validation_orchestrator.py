"""Complete offline validation pipeline and deployment gate."""
from __future__ import annotations

from dataclasses import dataclass
from time import monotonic
from typing import Any

from .completeness_checker import CompletenessChecker
from .coverage_tracker import CoverageTracker
from .cross_reference_validator import CrossReferenceValidator
from .deprecated_command_checker import DeprecatedCommandChecker
from .idempotency_checker import IdempotencyChecker
from .models import CoverageStatus, Severity, ValidationDiagnostic, ValidationReport, ValidationStage, ValidationStatus
from .secret_leak_scanner import SecretLeakScanner
from .semantic_validator import SemanticValidator
from .structural_validator import StructuralValidator
from .syntax_rule_engine import SyntaxRuleEngine


@dataclass(frozen=True)
class DeploymentGateResult:
    """Pre-deployment gate decision consumed by deployment orchestration."""

    allowed: bool
    reason: str
    report_status: ValidationStatus
    error_count: int
    warning_count: int
    coverage_percentage: float


class ValidationOrchestrator:
    """Run all offline checks in a deterministic order and expose coverage limits."""

    def __init__(self, grammar_root: str | None = None) -> None:
        self.structural = StructuralValidator()
        self.syntax = SyntaxRuleEngine(grammar_root)
        self.semantic = SemanticValidator()
        self.cross_reference = CrossReferenceValidator()
        self.secret_scanner = SecretLeakScanner()
        self.deprecated = DeprecatedCommandChecker()
        self.completeness = CompletenessChecker()
        self.idempotency = IdempotencyChecker()
        self.coverage = CoverageTracker()

    def validate(self, config_text: str, vendor: str, platform: str, device_model: str | None = None, platform_version: str | None = None, context: dict[str, Any] | None = None) -> ValidationReport:
        """Validate a configuration offline and return a deployment-gate report."""
        started = monotonic()
        context = dict(context or {})
        errors: list[ValidationDiagnostic] = []
        warnings: list[ValidationDiagnostic] = []
        info: list[ValidationDiagnostic] = []
        stage_results: dict[str, bool] = {}
        structural = self.structural.validate(config_text, vendor, platform)
        self._collect(structural.diagnostics, errors, warnings, info)
        stage_results[ValidationStage.STRUCTURAL.value] = structural.valid
        line_results = self.syntax.validate(config_text, vendor, platform)
        syntax_diagnostics = [diagnostic for result in line_results for diagnostic in result.diagnostics]
        self._collect(syntax_diagnostics, errors, warnings, info)
        stage_results[ValidationStage.SYNTAX.value] = not any(diagnostic.severity in {Severity.ERROR, Severity.CRITICAL} for diagnostic in syntax_diagnostics)
        semantic = self.semantic.validate(config_text, vendor, platform)
        self._collect(semantic, errors, warnings, info)
        stage_results[ValidationStage.SEMANTIC.value] = not any(diagnostic.severity in {Severity.ERROR, Severity.CRITICAL} for diagnostic in semantic)
        cross = self.cross_reference.validate(config_text, vendor, platform, context)
        self._collect(cross, errors, warnings, info)
        stage_results[ValidationStage.CROSS_REFERENCE.value] = not cross
        secret = self.secret_scanner.scan(config_text, vendor, platform)
        self._collect(secret, errors, warnings, info)
        stage_results[ValidationStage.SECRET_SCAN.value] = not secret
        deprecated = self.deprecated.check(config_text, vendor, platform, platform_version)
        self._collect(deprecated, errors, warnings, info)
        stage_results[ValidationStage.DEPRECATED.value] = not any(diagnostic.severity in {Severity.ERROR, Severity.CRITICAL} for diagnostic in deprecated)
        complete = self.completeness.check(config_text, vendor, platform, context.get("completeness_policy"))
        self._collect(complete, errors, warnings, info)
        stage_results[ValidationStage.COMPLETENESS.value] = not any(diagnostic.severity in {Severity.ERROR, Severity.CRITICAL} for diagnostic in complete)
        idempotency = self.idempotency.check(config_text, vendor, platform)
        self._collect(idempotency, errors, warnings, info)
        stage_results[ValidationStage.IDEMPOTENCY.value] = not any(diagnostic.severity in {Severity.ERROR, Severity.CRITICAL} for diagnostic in idempotency)
        generated_artifact = context.get("generated_artifact")
        if isinstance(generated_artifact, dict) and str(generated_artifact.get("status", "")).startswith("blocked"):
            errors.append(ValidationDiagnostic("GENERATION_ARTIFACT_BLOCKED", "Config generation artifact is already blocked and cannot enter a deployment gate.", Severity.ERROR, ValidationStage.SYNTAX, remediation="Resolve feature guard and capability evidence findings before validation."))
        feature_guard = context.get("feature_guard")
        feature_requests = context.get("feature_requests", [])
        if feature_guard is not None and isinstance(feature_requests, list):
            capability_evidence = context.get("capability_evidence", {})
            license_evidence = context.get("license_evidence", {})
            for request in feature_requests:
                guard_result = feature_guard.evaluate(dict(request), capability_evidence, license_evidence, platform, platform_version, bool(context.get("production", True)), context.get("decision_ids", ()))
                if not guard_result.allowed:
                    errors.append(ValidationDiagnostic("FEATURE_GUARD_BLOCKED", "A generated feature did not satisfy capability, license, command-source, or decision evidence gates.", Severity.ERROR, ValidationStage.SYNTAX, remediation="Resolve the feature guard findings before deployment.", metadata={"feature": guard_result.feature, "reasons": list(guard_result.reasons)}))
        capability_checker = context.get("capability_checker")
        if capability_checker is not None:
            equipment = context.get("equipment", {})
            equipment_requirements = context.get("equipment_requirements", context.get("requirements", {}))
            if isinstance(equipment, dict) and isinstance(equipment_requirements, dict):
                compatibility = capability_checker.check(equipment, equipment_requirements, production=bool(context.get("production", True)))
                if not compatibility.compatible:
                    errors.append(ValidationDiagnostic("CAPABILITY_NOT_CONFIRMED", "Required capability/license/compatibility evidence did not confirm the generated equipment path.", Severity.ERROR, ValidationStage.SYNTAX, remediation="Resolve equipment capability and license evidence before deployment.", metadata={"reasons": list(compatibility.reasons), "evidence_ids": list(compatibility.evidence_ids)}))
        template_registry = context.get("template_registry")
        template_ids = context.get("template_ids", [])
        if template_registry is not None and isinstance(template_ids, list):
            for template_id in template_ids:
                metadata = template_registry.get(str(template_id))
                if metadata is None:
                    errors.append(ValidationDiagnostic("TEMPLATE_NOT_REGISTERED", f"Template {template_id!r} is not present in the TemplateRegistry.", Severity.ERROR, ValidationStage.SYNTAX, remediation="Use a registered template with evidence metadata."))
                elif metadata.validation_state.value != "verified":
                    warnings.append(ValidationDiagnostic("TEMPLATE_NOT_PRODUCTION_VALIDATED", f"Template {template_id!r} is not model/version-authoritatively validated.", Severity.WARNING, ValidationStage.SYNTAX, remediation="Keep the artifact preview-only until authoritative model/version evidence is attached."))
        coverage_report = self.coverage.report(vendor, platform, line_results)
        uncovered = tuple(coverage_report["uncovered_commands"])
        duration_ms = int((monotonic() - started) * 1000)
        status = ValidationStatus.FAILED if errors else ValidationStatus.PASSED_WITH_WARNINGS if warnings or uncovered else ValidationStatus.PASSED
        gate = "allowed" if status is ValidationStatus.PASSED else "blocked"
        return ValidationReport(status, vendor, platform, device_model, platform_version, tuple(errors), tuple(warnings), tuple(info), float(coverage_report["coverage_percentage"]), uncovered, duration_ms, stage_results, gate)

    @staticmethod
    def _collect(diagnostics: list[ValidationDiagnostic] | tuple[ValidationDiagnostic, ...], errors: list[ValidationDiagnostic], warnings: list[ValidationDiagnostic], info: list[ValidationDiagnostic]) -> None:
        for diagnostic in diagnostics:
            if diagnostic.severity in {Severity.ERROR, Severity.CRITICAL}:
                errors.append(diagnostic)
            elif diagnostic.severity is Severity.WARNING:
                warnings.append(diagnostic)
            else:
                info.append(diagnostic)

    def validate_artifact(self, artifact: Any, context: dict[str, Any] | None = None) -> ValidationReport:
        """Validate a DeviceConfig/GenerationResult-like artifact without resolving secrets."""
        data = artifact
        if hasattr(artifact, "artifact"):
            data = artifact.artifact
        if hasattr(data, "to_dict"):
            data = data.to_dict()
        if not isinstance(data, dict):
            return ValidationReport(ValidationStatus.FAILED, "unknown", "unknown", None, None, (ValidationDiagnostic("INVALID_ARTIFACT", "The supplied object is not a serializable DeviceConfig artifact.", Severity.ERROR, ValidationStage.STRUCTURAL),), deployment_gate="blocked")
        merged = dict(context or {})
        merged["generated_artifact"] = data
        if data.get("unsupported_log"):
            merged["generated_artifact"] = data | {"status": "blocked_unsupported_features"}
        return self.validate(str(data.get("rendered_config", "")), str(data.get("vendor", "")), str(data.get("platform", "")), data.get("device_id"), data.get("os_version"), merged)

    @staticmethod
    def pre_deployment_gate(report: ValidationReport) -> DeploymentGateResult:
        """Return the deployment gate consumed by an external deployment orchestrator."""
        return DeploymentGateResult(report.can_deploy, "validation_passed_without_errors" if report.can_deploy else "validation_report_contains_errors_or_warnings_or_uncovered_commands", report.overall_status, len(report.errors), len(report.warnings), report.coverage_percentage)
