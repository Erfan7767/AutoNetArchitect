"""Evidence-gated firmware management for the AutoNetArchitect V1 workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from change_management.change_models import MaintenanceWindow
from log_redaction.redacting_filter import RedactingFilter


FirmwareDriver = Callable[[Mapping[str, Any]], Mapping[str, Any]]


class BootMode(str, Enum):
    """Firmware boot modes that may affect upgrade eligibility."""

    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"
    INSTALL = "install"
    BUNDLE = "bundle"
    PACKAGE = "package"
    BOOTLOADER = "bootloader"


class FirmwareOperationState(str, Enum):
    """States emitted by the limited V1 firmware workflow."""

    DRY_RUN = "dry_run"
    EXECUTED = "executed"
    FAILED = "failed"
    BLOCKED = "blocked"
    STAGED = "staged"


@dataclass(frozen=True)
class FirmwareImage:
    """A firmware artifact with an explicitly supplied integrity expectation."""

    image_id: str
    vendor: str
    platform: str
    model: str
    version: str
    expected_sha256: str
    artifact_reference: str = ""
    artifact_path: str = ""
    boot_mode: str = BootMode.UNKNOWN.value
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    release_date: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize image metadata without embedding artifact bytes."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "source_ids": list(self.source_ids)}


@dataclass(frozen=True)
class FirmwareTarget:
    """Exact device identity and operational context for one upgrade target."""

    target_id: str
    device_id: str
    vendor: str
    platform: str
    model: str
    current_version: str
    current_boot_mode: str = BootMode.UNKNOWN.value
    redundancy_group: str = ""
    redundancy_role: str = "standalone"
    site_id: str = ""
    management_reference: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize target identity and references."""
        return asdict(self)


@dataclass(frozen=True)
class UpgradePath:
    """One exact, evidence-backed current-to-target firmware path."""

    path_id: str
    vendor: str
    platform: str
    model: str
    current_version: str
    target_version: str
    source_boot_mode: str
    target_boot_mode: str
    support_state: str = "requires_evidence"
    rollback_image_id: str = ""
    evidence_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the exact path record."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids), "source_ids": list(self.source_ids)}


@dataclass(frozen=True)
class ImageIntegrityResult:
    """Hash verification result for a firmware image."""

    verified: bool
    status: str
    expected_sha256: str
    actual_sha256: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the integrity result."""
        return asdict(self)


@dataclass(frozen=True)
class FirmwareSafetyAssessment:
    """Conservative gate result before any firmware driver invocation."""

    allowed: bool
    safety_class: str
    reasons: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    required_prechecks: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize safety decisions and their evidence."""
        return asdict(self) | {"reasons": list(self.reasons), "required_human_inputs": list(self.required_human_inputs), "required_prechecks": list(self.required_prechecks), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class FirmwareUpgradeRequest:
    """Request for one exact firmware upgrade workflow."""

    request_id: str
    target: FirmwareTarget
    image: FirmwareImage
    maintenance_window: MaintenanceWindow | None = None
    approved: bool = False
    approval_reference: str = ""
    project_valid: bool = True
    unresolved_human_inputs: tuple[str, ...] = ()
    production_requested: bool = False
    dry_run: bool = True
    rollback_required: bool = True
    rollback_image_id: str = ""
    upgrade_path_id: str = ""
    actor: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize request metadata without reading or embedding image bytes."""
        return asdict(self) | {
            "target": self.target.to_dict(),
            "image": self.image.to_dict(),
            "maintenance_window": self.maintenance_window.to_dict() if self.maintenance_window else None,
            "unresolved_human_inputs": list(self.unresolved_human_inputs),
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True)
class FirmwareUpgradeOperation:
    """Result of one staged firmware operation."""

    operation_id: str
    request_id: str
    target_id: str
    state: str
    dry_run: bool
    executed: bool
    image_id: str
    target_version: str
    stage_number: int = 0
    output: str = ""
    provider_reference: str = ""
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    rollback_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize an operation without raw driver secrets."""
        return asdict(self) | {"reasons": list(self.reasons), "evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class FirmwareExecutionResult:
    """Final gate result for one firmware request."""

    request_id: str
    state: str
    gate: str
    operation: FirmwareUpgradeOperation | None
    safety: FirmwareSafetyAssessment
    integrity: ImageIntegrityResult
    path: UpgradePath | None
    required_human_inputs: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete safe result."""
        return {
            "request_id": self.request_id,
            "state": self.state,
            "gate": self.gate,
            "operation": self.operation.to_dict() if self.operation else None,
            "safety": self.safety.to_dict(),
            "integrity": self.integrity.to_dict(),
            "path": self.path.to_dict() if self.path else None,
            "required_human_inputs": list(self.required_human_inputs),
            "reasons": list(self.reasons),
            "evidence_ids": list(self.evidence_ids),
        }


class FirmwareManager:
    """Manage only registered, exact, evidence-backed firmware paths in V1."""

    def __init__(self, *, safety_checks: Any | None = None, audit_trail: Any | None = None) -> None:
        """Create an in-memory registry with optional safety and audit integrations."""
        self.images: dict[str, FirmwareImage] = {}
        self.paths: dict[str, UpgradePath] = {}
        self.audit_trail = audit_trail
        self._in_flight_redundancy_groups: set[str] = set()
        if safety_checks is None:
            from .safety_checks import FirmwareSafetyChecks

            safety_checks = FirmwareSafetyChecks()
        self.safety_checks = safety_checks

    def register_image(self, image: FirmwareImage) -> FirmwareImage:
        """Register one image metadata record; no artifact is executed or downloaded."""
        if not image.image_id or not image.vendor or not image.platform or not image.model or not image.version:
            raise ValueError("image identity fields are mandatory")
        self.images[image.image_id] = image
        return image

    def register_upgrade_path(self, path: UpgradePath) -> UpgradePath:
        """Register one exact path without treating it as supported automatically."""
        if not path.path_id or not path.vendor or not path.platform or not path.model or not path.current_version or not path.target_version:
            raise ValueError("upgrade path exact identity fields are mandatory")
        self.paths[path.path_id] = path
        return path

    def verify_image(self, image: FirmwareImage, artifact_bytes: bytes | None = None) -> ImageIntegrityResult:
        """Verify SHA-256 from supplied bytes or a local artifact path."""
        expected = image.expected_sha256.strip().lower()
        if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
            return ImageIntegrityResult(False, "invalid_expected_sha256", expected, reason="expected SHA-256 is not a valid 64-character hexadecimal digest")
        payload = artifact_bytes
        if payload is None and image.artifact_path:
            try:
                payload = Path(image.artifact_path).read_bytes()
            except OSError:
                return ImageIntegrityResult(False, "artifact_unreadable", expected, reason="firmware artifact path could not be read")
        if payload is None:
            return ImageIntegrityResult(False, "not_verifiable_with_current_inputs", expected, reason="artifact bytes or a readable artifact path were not supplied")
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            return ImageIntegrityResult(False, "hash_mismatch", expected, actual, "computed SHA-256 does not match the supplied image digest")
        return ImageIntegrityResult(True, "verified", expected, actual, "SHA-256 integrity verified")

    def resolve_path(self, request: FirmwareUpgradeRequest) -> UpgradePath | None:
        """Resolve only an exact registered path; no version-range guessing is performed."""
        candidates = list(self.paths.values())
        if request.upgrade_path_id:
            candidates = [self.paths[request.upgrade_path_id]] if request.upgrade_path_id in self.paths else []
        for path in candidates:
            if self._path_matches(request.target, request.image, path):
                return path
        return None

    def execute(self, request: FirmwareUpgradeRequest, *, driver: FirmwareDriver | None = None, artifact_bytes: bytes | None = None, stage_number: int = 0) -> FirmwareExecutionResult:
        """Run a dry-run or approved production-safe operation through an explicit driver."""
        integrity = self.verify_image(request.image, artifact_bytes)
        path = self.resolve_path(request)
        assessment = self.safety_checks.assess(request, path, integrity, tuple(self._in_flight_redundancy_groups))
        evidence = tuple(dict.fromkeys(request.evidence_ids + request.image.evidence_ids + (path.evidence_ids if path else ())))
        if not assessment.allowed:
            operation = FirmwareUpgradeOperation(f"{request.request_id}:blocked", request.request_id, request.target.target_id, FirmwareOperationState.BLOCKED.value, request.dry_run, False, request.image.image_id, request.image.version, stage_number, reasons=assessment.reasons, evidence_ids=evidence, rollback_available=bool(request.rollback_image_id or (path and path.rollback_image_id)))
            result = FirmwareExecutionResult(request.request_id, FirmwareOperationState.BLOCKED.value, "blocked", operation, assessment, integrity, path, assessment.required_human_inputs, assessment.reasons, evidence)
            self._audit(request, result)
            return result
        if request.dry_run:
            operation = FirmwareUpgradeOperation(f"{request.request_id}:dry-run", request.request_id, request.target.target_id, FirmwareOperationState.DRY_RUN.value, True, False, request.image.image_id, request.image.version, stage_number, output="dry-run only; no firmware driver invoked", reasons=("dry-run mode selected",), evidence_ids=evidence, rollback_available=bool(request.rollback_image_id or (path and path.rollback_image_id)))
            result = FirmwareExecutionResult(request.request_id, FirmwareOperationState.DRY_RUN.value, "review_only", operation, assessment, integrity, path, (), ("dry-run mode selected",), evidence)
            self._audit(request, result)
            return result
        group = request.target.redundancy_group
        if group:
            self._in_flight_redundancy_groups.add(group)
        try:
            if driver is None:
                operation = FirmwareUpgradeOperation(f"{request.request_id}:driver-blocked", request.request_id, request.target.target_id, FirmwareOperationState.BLOCKED.value, False, False, request.image.image_id, request.image.version, stage_number, reasons=("firmware driver is not configured",), evidence_ids=evidence, rollback_available=bool(request.rollback_image_id or (path and path.rollback_image_id)))
                result = FirmwareExecutionResult(request.request_id, FirmwareOperationState.BLOCKED.value, "blocked", operation, assessment, integrity, path, ("firmware_driver",), operation.reasons, evidence)
                self._audit(request, result)
                return result
            try:
                response = dict(driver(self._safe_payload(request, path, stage_number)))
                output_value = RedactingFilter.sanitize_value(response.get("output", ""))
                output = output_value if isinstance(output_value, str) else str(output_value)
                successful = str(response.get("state", response.get("status", ""))).lower() in {"success", "successful", "executed", "ok"}
                state = FirmwareOperationState.EXECUTED.value if successful else FirmwareOperationState.FAILED.value
                reasons = tuple(str(item) for item in response.get("reasons", ()))
                response_evidence = tuple(str(item) for item in response.get("evidence_ids", ()))
                all_evidence = tuple(dict.fromkeys(evidence + response_evidence))
                operation = FirmwareUpgradeOperation(f"{request.request_id}:operation", request.request_id, request.target.target_id, state, False, True, request.image.image_id, request.image.version, stage_number, output, str(response.get("provider_reference", "")), reasons, all_evidence, bool(request.rollback_image_id or (path and path.rollback_image_id)))
                result = FirmwareExecutionResult(request.request_id, state, "allow" if successful else "block_or_review", operation, assessment, integrity, path, (), reasons, all_evidence)
                self._audit(request, result)
                return result
            except Exception:
                operation = FirmwareUpgradeOperation(f"{request.request_id}:failed", request.request_id, request.target.target_id, FirmwareOperationState.FAILED.value, False, True, request.image.image_id, request.image.version, stage_number, reasons=("firmware driver failed without exposing runtime details",), evidence_ids=evidence, rollback_available=bool(request.rollback_image_id or (path and path.rollback_image_id)))
                result = FirmwareExecutionResult(request.request_id, FirmwareOperationState.FAILED.value, "block_or_review", operation, assessment, integrity, path, (), operation.reasons, evidence)
                self._audit(request, result)
                return result
        finally:
            if group:
                self._in_flight_redundancy_groups.discard(group)

    @staticmethod
    def _path_matches(target: FirmwareTarget, image: FirmwareImage, path: UpgradePath) -> bool:
        """Match all exact path dimensions, including boot modes."""
        return (
            path.vendor.lower() == target.vendor.lower() == image.vendor.lower()
            and path.platform.lower() == target.platform.lower() == image.platform.lower()
            and path.model.lower() == target.model.lower() == image.model.lower()
            and path.current_version == target.current_version
            and path.target_version == image.version
            and path.source_boot_mode == target.current_boot_mode
            and path.target_boot_mode == image.boot_mode
        )

    @staticmethod
    def _safe_payload(request: FirmwareUpgradeRequest, path: UpgradePath | None, stage_number: int) -> dict[str, Any]:
        """Build a driver payload containing references and exact metadata only."""
        return {
            "request_id": request.request_id,
            "target_id": request.target.target_id,
            "device_id": request.target.device_id,
            "vendor": request.target.vendor,
            "platform": request.target.platform,
            "model": request.target.model,
            "current_version": request.target.current_version,
            "target_version": request.image.version,
            "image_id": request.image.image_id,
            "image_reference": request.image.artifact_reference,
            "artifact_path": request.image.artifact_path,
            "current_boot_mode": request.target.current_boot_mode,
            "target_boot_mode": request.image.boot_mode,
            "upgrade_path_id": path.path_id if path else "",
            "rollback_image_id": request.rollback_image_id or (path.rollback_image_id if path else ""),
            "maintenance_window": request.maintenance_window.to_dict() if request.maintenance_window else None,
            "approval_reference": request.approval_reference,
            "stage_number": stage_number,
            "evidence_ids": list(request.evidence_ids + request.image.evidence_ids + (path.evidence_ids if path else ())),
        }

    def _audit(self, request: FirmwareUpgradeRequest, result: FirmwareExecutionResult) -> None:
        """Record secret-safe firmware metadata when an audit integration is supplied."""
        if self.audit_trail is None:
            return
        details = {"request_id": request.request_id, "target_id": request.target.target_id, "device_id": request.target.device_id, "vendor": request.target.vendor, "platform": request.target.platform, "model": request.target.model, "current_version": request.target.current_version, "target_version": request.image.version, "image_id": request.image.image_id, "path_id": result.path.path_id if result.path else "", "state": result.state, "gate": result.gate, "stage_number": result.operation.stage_number if result.operation else 0, "evidence_ids": list(result.evidence_ids)}
        self.audit_trail.record("firmware.upgrade", request.actor or "firmware_manager", details, outcome=result.state)
