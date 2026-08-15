"""Reconcile lifecycle asset records without silently accepting operational drift."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping

from .discovery_models import DeviceProfile, ReconciliationStatus


class LifecycleStage(str, Enum):
    """Governed lifecycle stages reconciled by this module."""

    DESIGN = "design"
    PURCHASED = "purchased"
    INSTALLED = "installed"
    DISCOVERED = "discovered"
    OPERATIONAL = "operational"


@dataclass(frozen=True)
class LifecycleRecord:
    """One normalized record from a lifecycle source of truth."""

    asset_id: str
    stage: str
    vendor: str = ""
    platform: str = ""
    model: str = ""
    version: str = ""
    serial: str = ""
    hostname: str = ""
    status: str = ""
    attributes: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the record for audit or persistence."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class ReconciliationFinding:
    """One explicit mismatch or evidence gap."""

    asset_id: str
    status: str
    stage: str
    reason: str
    expected: dict[str, Any] = field(default_factory=dict)
    observed: dict[str, Any] = field(default_factory=dict)
    differing_fields: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    required_human_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize one finding."""
        return asdict(self) | {"differing_fields": list(self.differing_fields), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class ReconciliationReport:
    """Complete lifecycle reconciliation report and deployment gate."""

    status: str
    production_gate: str
    findings: tuple[ReconciliationFinding, ...]
    compared_assets: tuple[str, ...]
    evidence_basis: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize a report without losing uncertainty details."""
        return {
            "status": self.status,
            "production_gate": self.production_gate,
            "findings": [finding.to_dict() for finding in self.findings],
            "compared_assets": list(self.compared_assets),
            "evidence_basis": list(self.evidence_basis),
        }


class ReconciliationEngine:
    """Compare lifecycle records and discovered profiles with conservative gates."""

    COMPARED_FIELDS = ("vendor", "platform", "model", "version", "serial", "hostname")
    STAGES = tuple(stage.value for stage in LifecycleStage)

    def reconcile(
        self,
        design: Mapping[str, LifecycleRecord | Mapping[str, Any]] | None = None,
        purchased: Mapping[str, LifecycleRecord | Mapping[str, Any]] | None = None,
        installed: Mapping[str, LifecycleRecord | Mapping[str, Any]] | None = None,
        discovered: Mapping[str, DeviceProfile | LifecycleRecord | Mapping[str, Any]] | None = None,
        operational: Mapping[str, LifecycleRecord | Mapping[str, Any]] | None = None,
    ) -> ReconciliationReport:
        """Reconcile all supplied lifecycle stages by stable asset identifier."""
        normalized: dict[str, dict[str, LifecycleRecord]] = {stage: {} for stage in self.STAGES}
        for stage, source in (("design", design), ("purchased", purchased), ("installed", installed), ("discovered", discovered), ("operational", operational)):
            for asset_id, raw in (source or {}).items():
                normalized[stage][asset_id] = self._normalize(asset_id, stage, raw)
        asset_ids = tuple(sorted(set().union(*(set(records) for records in normalized.values()))))
        findings: list[ReconciliationFinding] = []
        evidence: set[str] = set()
        for asset_id in asset_ids:
            findings.extend(self._reconcile_asset(asset_id, normalized, evidence))
        if not asset_ids:
            status = ReconciliationStatus.INSUFFICIENT_EVIDENCE.value
        elif any(finding.status in {ReconciliationStatus.AMBIGUOUS.value, ReconciliationStatus.UNKNOWN.value, ReconciliationStatus.UNSUPPORTED.value, ReconciliationStatus.INSUFFICIENT_EVIDENCE.value} for finding in findings):
            status = ReconciliationStatus.INSUFFICIENT_EVIDENCE.value
        elif any(finding.status in {ReconciliationStatus.DRIFT.value, ReconciliationStatus.MISSING_FROM_DISCOVERED.value, ReconciliationStatus.UNEXPECTED_DISCOVERED.value} for finding in findings):
            status = ReconciliationStatus.DRIFT.value
        else:
            status = ReconciliationStatus.ALIGNED.value
        return ReconciliationReport(status, "allow" if status == ReconciliationStatus.ALIGNED.value else "block_or_review", tuple(findings), asset_ids, tuple(sorted(evidence)))

    def _reconcile_asset(self, asset_id: str, records: dict[str, dict[str, LifecycleRecord]], evidence: set[str]) -> list[ReconciliationFinding]:
        """Produce findings for one asset across adjacent lifecycle stages."""
        findings: list[ReconciliationFinding] = []
        present = {stage: records[stage].get(asset_id) for stage in self.STAGES}
        for record in present.values():
            if record:
                evidence.update(record.evidence_ids)
        discovered_record = present["discovered"]
        if discovered_record and discovered_record.status in {"unsupported_vendor", "unsupported", ReconciliationStatus.UNSUPPORTED.value}:
            findings.append(ReconciliationFinding(asset_id, ReconciliationStatus.UNSUPPORTED.value, "discovered", "device vendor or parser is not validated for production reconciliation", {}, discovered_record.to_dict(), required_human_action="provide validated vendor evidence or keep the device on preview-only handling"))
        if discovered_record and discovered_record.status in {"unknown_device", "ambiguous", ReconciliationStatus.AMBIGUOUS.value, ReconciliationStatus.UNKNOWN.value}:
            findings.append(ReconciliationFinding(asset_id, ReconciliationStatus.AMBIGUOUS.value, "discovered", "discovered identity is ambiguous and cannot be promoted to a fact", {}, discovered_record.to_dict(), required_human_action="supply an authoritative device output or human identity confirmation"))
        if present["design"] and not discovered_record:
            findings.append(ReconciliationFinding(asset_id, ReconciliationStatus.MISSING_FROM_DISCOVERED.value, "discovered", "designed asset was not found in the discovery evidence", present["design"].to_dict(), {}, evidence_ids=present["design"].evidence_ids, required_human_action="confirm device access, installation state, or asset identifier"))
        if not present["design"] and discovered_record:
            findings.append(ReconciliationFinding(asset_id, ReconciliationStatus.UNEXPECTED_DISCOVERED.value, "discovered", "discovered asset has no matching design record", {}, discovered_record.to_dict(), evidence_ids=discovered_record.evidence_ids, required_human_action="confirm authorization and add the asset to the governed design or quarantine it"))
        ordered_present = [(stage, present[stage]) for stage in self.STAGES if present[stage] is not None]
        for (left_stage, left), (right_stage, right) in zip(ordered_present, ordered_present[1:]):
            findings.extend(self._compare_pair(asset_id, left_stage, right_stage, left, right))
        if not findings and present["discovered"]:
            findings.append(ReconciliationFinding(asset_id, ReconciliationStatus.ALIGNED.value, "discovered", "all supplied lifecycle identity fields agree", present["discovered"].to_dict(), present["discovered"].to_dict(), evidence_ids=present["discovered"].evidence_ids))
        return findings

    def _compare_pair(self, asset_id: str, left_stage: str, right_stage: str, left: LifecycleRecord, right: LifecycleRecord) -> list[ReconciliationFinding]:
        """Compare identity and operational state between two adjacent stages."""
        differences = tuple(field for field in self.COMPARED_FIELDS if getattr(left, field) and getattr(right, field) and getattr(left, field) != getattr(right, field))
        if differences:
            return [ReconciliationFinding(asset_id, ReconciliationStatus.DRIFT.value, right_stage, f"{right_stage} differs from {left_stage}", left.to_dict(), right.to_dict(), differences, tuple(sorted(set(left.evidence_ids + right.evidence_ids))), "review the mismatch and approve a governed change before deployment")]
        if right_stage == "operational":
            healthy = right.attributes.get("healthy", right.status.lower() in {"healthy", "up", "operational"})
            if not isinstance(healthy, bool):
                return [ReconciliationFinding(asset_id, ReconciliationStatus.INSUFFICIENT_EVIDENCE.value, right_stage, "operational health observation is not a boolean", left.to_dict(), right.to_dict(), evidence_ids=right.evidence_ids, required_human_action="provide an explicit operational health observation")]
            if not healthy:
                return [ReconciliationFinding(asset_id, ReconciliationStatus.DRIFT.value, right_stage, "operational record reports an unhealthy state", left.to_dict(), right.to_dict(), evidence_ids=right.evidence_ids, required_human_action="investigate the operational fault and complete verification")]
        return []

    @staticmethod
    def _normalize(asset_id: str, stage: str, raw: LifecycleRecord | DeviceProfile | Mapping[str, Any]) -> LifecycleRecord:
        """Normalize profiles and dictionaries without filling missing identity values."""
        if isinstance(raw, LifecycleRecord):
            return raw
        if isinstance(raw, DeviceProfile):
            return LifecycleRecord(asset_id, stage, raw.vendor, raw.platform, raw.model, raw.version, raw.serial, raw.hostname, raw.status, {"profile_confidence": raw.confidence, "safe_for_production": raw.safe_for_production, "ambiguous_fields": list(raw.ambiguous_fields)}, (raw.evidence_hash,) if raw.evidence_hash else ())
        if not isinstance(raw, Mapping):
            raise TypeError("lifecycle record must be LifecycleRecord, DeviceProfile, or mapping")
        values = {field: raw.get(field, "") for field in ReconciliationEngine.COMPARED_FIELDS}
        attributes = dict(raw.get("attributes", {}))
        for key in ("healthy", "profile_confidence", "safe_for_production", "ambiguous_fields"):
            if key in raw:
                attributes[key] = raw[key]
        evidence_ids = tuple(str(value) for value in raw.get("evidence_ids", ()))
        return LifecycleRecord(asset_id, stage, *(str(values[field]) for field in ReconciliationEngine.COMPARED_FIELDS), str(raw.get("status", "")), attributes, evidence_ids)
