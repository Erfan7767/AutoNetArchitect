"""Capability and feature gates for configuration generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class GuardResult:
    """Auditable result of checking one requested configuration feature."""

    feature: str
    allowed: bool
    reasons: tuple[str, ...] = ()
    capability_evidence_ids: tuple[str, ...] = ()
    license_evidence_ids: tuple[str, ...] = ()
    decision_ids: tuple[str, ...] = ()
    command_source_ids: tuple[str, ...] = ()


class FeatureGuards:
    """Reject unsupported or untraceable features before rendering any command."""

    VERIFIED_STATES = {"verified", "supported", "supported_with_license"}

    @staticmethod
    def _ids(value: Any) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,) if value else ()
        if isinstance(value, dict):
            values = value.get("ids", value.get("decision_ids", value.get("evidence_ids", [])))
            return FeatureGuards._ids(values)
        if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
            return tuple(str(item) for item in value if str(item))
        return ()

    @classmethod
    def _verified_evidence(cls, record: Any) -> tuple[bool, tuple[str, ...]]:
        if not isinstance(record, dict):
            return False, ()
        state = str(record.get("verification_state", record.get("status", ""))).lower()
        evidence_ids = cls._ids(record.get("evidence_ids"))
        revoked = bool(record.get("revoked", False))
        expired = bool(record.get("expired", False))
        return state in cls.VERIFIED_STATES and bool(evidence_ids) and not revoked and not expired, evidence_ids

    def evaluate(
        self,
        feature_request: dict[str, Any],
        capability_evidence: dict[str, Any],
        license_evidence: dict[str, Any],
        platform: str,
        os_version: str | None,
        production: bool = True,
        default_decision_ids: Iterable[str] = (),
    ) -> GuardResult:
        """Evaluate a feature without guessing commands or capability support."""
        feature = str(feature_request.get("feature", "unidentified_feature"))
        capability = str(feature_request.get("capability", ""))
        reasons: list[str] = []
        capability_ids: tuple[str, ...] = ()
        license_ids: tuple[str, ...] = ()
        decision_ids = self._ids(feature_request.get("decision_ids")) or tuple(str(item) for item in default_decision_ids)
        command_source_ids = self._ids(feature_request.get("command_source_ids"))
        if not capability:
            reasons.append("capability_reference_missing")
        record = capability_evidence.get(capability)
        usable, capability_ids = self._verified_evidence(record)
        if not usable:
            reasons.append("capability_evidence_missing_unverified_expired_or_revoked")
        elif isinstance(record, dict):
            record_platform = record.get("platform")
            if record_platform and str(record_platform).lower() != platform.lower():
                reasons.append("capability_platform_scope_mismatch")
            record_version = record.get("version")
            if record_version and os_version and str(record_version) != str(os_version):
                reasons.append("capability_version_scope_mismatch")
        if str(feature_request.get("support_state", "supported")).lower() in {"unsupported", "unknown", "not_supported"}:
            reasons.append("feature_explicitly_unsupported")
        required_license = feature_request.get("required_license", feature_request.get("license_id"))
        if required_license:
            license_record = license_evidence.get(str(required_license))
            license_ok, license_ids = self._verified_evidence(license_record)
            if not license_ok:
                reasons.append("required_license_evidence_missing_unverified_expired_or_revoked")
            elif isinstance(license_record, dict) and not bool(license_record.get("production_eligible", True)) and production:
                reasons.append("required_license_not_production_eligible")
        commands = feature_request.get("commands")
        if not isinstance(commands, list) or not commands or not all(isinstance(command, str) and command.strip() for command in commands):
            reasons.append("exact_commands_missing_or_not_a_string_list")
        if production and not command_source_ids:
            reasons.append("command_syntax_evidence_missing")
        if not decision_ids:
            reasons.append("design_decision_reference_missing")
        return GuardResult(feature, not reasons, tuple(dict.fromkeys(reasons)), capability_ids, license_ids, decision_ids, command_source_ids)

    def unsupported_entry(self, result: GuardResult, workflow: str) -> dict[str, Any]:
        """Convert a failed result into an explicit unsupported log entry."""
        return {
            "feature": result.feature,
            "workflow": workflow,
            "reasons": list(result.reasons),
            "required_action": "provide_verified_capability_license_command_evidence_and_design_decision_or keep feature out of production config",
            "capability_evidence_ids": list(result.capability_evidence_ids),
            "license_evidence_ids": list(result.license_evidence_ids),
            "decision_ids": list(result.decision_ids),
            "command_source_ids": list(result.command_source_ids),
        }
