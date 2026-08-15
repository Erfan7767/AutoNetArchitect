"""Cross-check equipment, capabilities, licenses, and optics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability_matrix import CapabilityMatrix
from .licensing_db import LicensingDB


@dataclass(frozen=True)
class CompatibilityReport:
    """Auditable compatibility result."""

    compatible: bool
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    confidence: float = 0.0
    missing_human_inputs: tuple[str, ...] = ()
    checks: dict[str, str] = field(default_factory=dict)


class CompatibilityChecker:
    """Prevent unsupported combinations from reaching a production selection."""

    def __init__(self, capability_matrix: CapabilityMatrix | None = None, licensing_db: LicensingDB | None = None, optics_catalog: list[dict[str, Any]] | None = None) -> None:
        self.capability_matrix = capability_matrix or CapabilityMatrix()
        self.licensing_db = licensing_db or LicensingDB()
        self.optics_catalog = list(optics_catalog or [])

    def _optic_supported(self, vendor: str, model: str, optic: dict[str, Any], production: bool) -> bool:
        identifier = str(optic.get("optic_id", optic.get("part_number", ""))).lower()
        for item in self.optics_catalog:
            if str(item.get("optic_id", item.get("part_number", ""))).lower() != identifier:
                continue
            if str(item.get("vendor", "")).lower() != vendor.lower():
                continue
            if model.lower() not in {str(value).lower() for value in item.get("compatible_models", [])}:
                continue
            if production and not bool(item.get("production_eligible", False)):
                continue
            if item.get("verification_state") != "verified" or not item.get("evidence_ids"):
                continue
            return True
        return False

    def check(self, equipment: dict[str, Any], requirements: dict[str, Any], production: bool = True) -> CompatibilityReport:
        """Evaluate one candidate against a requirement set."""
        vendor = str(equipment.get("vendor", ""))
        platform = str(equipment.get("platform", ""))
        model = str(equipment.get("model", ""))
        version = equipment.get("version", requirements.get("version"))
        reasons: list[str] = []
        evidence: list[str] = []
        missing: list[str] = []
        checks: dict[str, str] = {}
        vendor_state = str(equipment.get("vendor_status", ""))
        if not vendor:
            reasons.append("vendor_missing")
        if not platform or not model:
            reasons.append("platform_or_model_missing")
        if production and (not bool(equipment.get("production_eligible", False)) or vendor_state in {"unsupported", "not_production_approved", "catalogued_not_production_approved"}):
            reasons.append("vendor_or_equipment_not_production_approved")
        required_features = [str(value) for value in requirements.get("required_capabilities", requirements.get("capabilities", []))]
        if production and not required_features:
            missing.append("required_capabilities")
            reasons.append("production_capability_requirements_missing")
        license_id = requirements.get("license_id", equipment.get("license_id"))
        feature_confidences: list[float] = []
        for feature in required_features:
            result = self.capability_matrix.supports(vendor, platform, model, version, feature, license_id, require_verified_evidence=production)
            checks[f"capability:{feature}"] = result.reason
            if not result.supported:
                reasons.append(f"capability:{feature}:{result.reason}")
            else:
                evidence.extend(result.evidence_chain)
                feature_confidences.append(result.confidence)
            if result.reason == "required_license_missing":
                missing.append("license_id")
        if required_features and license_id:
            for feature in required_features:
                entitlement = self.licensing_db.has_verified_entitlement(vendor, str(license_id), feature, production=production)
                checks[f"license:{feature}"] = entitlement[1]
                if not entitlement[0]:
                    reasons.append(f"license:{feature}:{entitlement[1]}")
                else:
                    evidence.extend(entitlement[2])
                    feature_confidences.append(entitlement[3])
        elif required_features and production:
            reasons.append("license_scope_not_resolved")
        for optic in requirements.get("required_optics", equipment.get("required_optics", [])):
            if not self._optic_supported(vendor, model, dict(optic), production):
                reasons.append(f"optic_not_evidenced:{optic.get('optic_id', optic.get('part_number', 'unknown'))}")
            else:
                evidence.extend(str(value) for value in optic.get("evidence_ids", []))
        if not version:
            missing.append("equipment_version")
            if production:
                reasons.append("equipment_version_missing")
        unique_evidence = tuple(dict.fromkeys(evidence))
        compatible = not reasons
        confidence = min(feature_confidences) if compatible and feature_confidences else (0.0 if not compatible else float(equipment.get("confidence", 0.0)))
        return CompatibilityReport(compatible, tuple(reasons), unique_evidence, confidence, tuple(dict.fromkeys(missing)), checks)
