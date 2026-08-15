"""Out-of-band management design with human-supplied endpoint boundaries."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class OOBStatus(str, Enum):
    """Design outcomes for OOB management."""

    READY_FOR_REVIEW = "ready_for_review"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True)
class OOBPath:
    """One OOB path to one device using an explicit human reference."""

    path_id: str
    device_id: str
    transport: str
    endpoint_reference: str
    role: str
    primary: bool
    authentication_reference: str = ""
    evidence_ids: tuple[str, ...] = ()
    fallback_path_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize an OOB path without resolving credentials."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class OOBDesign:
    """Versioned OOB design artifact with explicit uncertainty and review gate."""

    design_id: str
    status: str
    site_id: str
    paths: tuple[OOBPath, ...]
    transport_scope: tuple[str, ...]
    redundancy_required: bool
    production_safe_claim_allowed: bool
    required_human_inputs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ("OOB design does not establish carrier availability", "endpoint references remain human-owned inputs", "design does not authorize remote changes")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the OOB design."""
        return {"design_id": self.design_id, "status": self.status, "site_id": self.site_id, "paths": [path.to_dict() for path in self.paths], "transport_scope": list(self.transport_scope), "redundancy_required": self.redundancy_required, "production_safe_claim_allowed": self.production_safe_claim_allowed, "required_human_inputs": list(self.required_human_inputs), "assumptions": list(self.assumptions), "evidence_ids": list(self.evidence_ids), "limitations": list(self.limitations)}


class OOBDesigner:
    """Build a reviewable OOB management model without inventing physical details."""

    def design(
        self,
        site_id: str,
        devices: Sequence[Mapping[str, Any]] | None,
        *,
        transport_scope: Sequence[str] | None = None,
        redundancy_required: bool = True,
        evidence_ids: Sequence[str] = (),
    ) -> OOBDesign:
        """Create OOB paths from explicit device endpoint references."""
        missing: list[str] = []
        if not site_id:
            missing.append("site_id")
        if not devices:
            missing.append("devices")
        if not transport_scope:
            missing.append("transport_scope")
        if missing:
            return OOBDesign(f"oob:blocked:{site_id or 'unknown'}", OOBStatus.BLOCKED_MISSING_HUMAN_DATA.value, site_id, (), tuple(str(item) for item in (transport_scope or ())), redundancy_required, False, tuple(missing), ("OOB endpoint values are not inferred",), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        paths: list[OOBPath] = []
        for index, device in enumerate(devices, start=1):
            device_id = str(device.get("device_id", ""))
            endpoint = str(device.get("endpoint_reference", ""))
            transport = str(device.get("transport", ""))
            if not device_id or not endpoint or not transport:
                missing.extend(f"device_{index}_device_id_or_endpoint_or_transport" for _ in (0,))
                continue
            auth_ref = str(device.get("authentication_reference", ""))
            if auth_ref and not auth_ref.startswith("secret://"):
                missing.append(f"device_{device_id}_authentication_reference_must_be_secret_reference")
            paths.append(OOBPath(str(device.get("path_id", f"oob:{site_id}:{device_id}")), device_id, transport, endpoint, str(device.get("role", "primary_management")), bool(device.get("primary", True)), auth_ref, tuple(str(item) for item in device.get("evidence_ids", ())), str(device.get("fallback_path_id", ""))))
        if missing:
            return OOBDesign(f"oob:blocked:{site_id}", OOBStatus.BLOCKED_MISSING_HUMAN_DATA.value, site_id, tuple(paths), tuple(str(item) for item in transport_scope), redundancy_required, False, tuple(dict.fromkeys(missing)), ("incomplete OOB inputs cannot be promoted to a deployment path",), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        if redundancy_required:
            devices_with_paths = {path.device_id for path in paths}
            missing_fallback = tuple(sorted(device_id for device_id in devices_with_paths if sum(path.device_id == device_id for path in paths) < 2))
            if missing_fallback:
                return OOBDesign(f"oob:review:{site_id}", OOBStatus.INSUFFICIENT_EVIDENCE.value, site_id, tuple(paths), tuple(str(item) for item in transport_scope), True, False, tuple(f"redundant_oob_path:{device_id}" for device_id in missing_fallback), ("redundancy was requested but a second explicit path was not supplied",), tuple(dict.fromkeys(str(item) for item in evidence_ids)))
        combined_evidence = tuple(str(item) for item in tuple(evidence_ids) + tuple(item for path in paths for item in path.evidence_ids))
        return OOBDesign(f"oob:{site_id}", OOBStatus.READY_FOR_REVIEW.value, site_id, tuple(paths), tuple(str(item) for item in transport_scope), redundancy_required, False, (), ("OOB path availability and carrier/service continuity require human validation",), tuple(dict.fromkeys(combined_evidence)))
