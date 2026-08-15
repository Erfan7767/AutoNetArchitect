"""Shared contracts for vendor-family bootstrap planning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence


class BootstrapStatus(str, Enum):
    """Outcomes for bootstrap planning."""

    PREVIEW_ONLY = "preview_only"
    READY_FOR_REVIEW = "ready_for_review"
    BLOCKED_MISSING_HUMAN_DATA = "blocked_missing_human_data"
    BLOCKED_UNSUPPORTED_VENDOR = "blocked_unsupported_vendor"
    BLOCKED_REMOTE_DESTRUCTIVE = "blocked_remote_destructive"


@dataclass(frozen=True)
class BootstrapRequest:
    """Human-scoped bootstrap request with no embedded secret values."""

    device_id: str
    vendor: str
    platform: str
    model: str = ""
    endpoint_reference: str = ""
    oob_reference: str = ""
    credential_reference: str = ""
    console_available: bool = False
    desired_controls: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    validated_command_evidence_ids: tuple[str, ...] = ()
    production_requested: bool = False
    remote_destructive: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the request without resolving credentials."""
        return asdict(self) | {"desired_controls": list(self.desired_controls), "evidence_ids": list(self.evidence_ids), "validated_command_evidence_ids": list(self.validated_command_evidence_ids)}


@dataclass(frozen=True)
class BootstrapStep:
    """Vendor-family bootstrap intent step, not an invented CLI command."""

    step_id: str
    title: str
    action_intent: str
    requires_console_or_oob: bool
    destructive: bool
    validation_checks: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize one bootstrap intent step."""
        return asdict(self) | {"validation_checks": list(self.validation_checks)}


@dataclass(frozen=True)
class BootstrapArtifact:
    """Versioned bootstrap planning artifact with production boundary metadata."""

    artifact_id: str
    status: str
    vendor: str
    platform: str
    device_id: str
    production_deployable: bool
    remote_destructive_allowed: bool
    steps: tuple[BootstrapStep, ...] = ()
    exact_commands: tuple[str, ...] = ()
    required_human_inputs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    secret_references: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ("bootstrap artifact expresses intent; vendor syntax requires validated command evidence", "artifact is not production change approval")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the artifact without secret resolution."""
        return {"artifact_id": self.artifact_id, "status": self.status, "vendor": self.vendor, "platform": self.platform, "device_id": self.device_id, "production_deployable": self.production_deployable, "remote_destructive_allowed": self.remote_destructive_allowed, "steps": [step.to_dict() for step in self.steps], "exact_commands": list(self.exact_commands), "required_human_inputs": list(self.required_human_inputs), "assumptions": list(self.assumptions), "evidence_ids": list(self.evidence_ids), "secret_references": list(self.secret_references), "limitations": list(self.limitations)}


class VendorBootstrapWorkflow:
    """Base workflow that creates safe generic bootstrap intents for a vendor family."""

    vendor = ""
    platform_aliases: tuple[str, ...] = ()
    family_name = ""

    def build(self, request: BootstrapRequest) -> BootstrapArtifact:
        """Build a vendor-specific intent artifact with no fabricated commands."""
        missing = self._missing(request)
        if request.remote_destructive:
            return self._blocked(request, BootstrapStatus.BLOCKED_REMOTE_DESTRUCTIVE.value, ("remote_destructive operations are blocked by policy",))
        if request.production_requested:
            return self._blocked(request, BootstrapStatus.PREVIEW_ONLY.value, ("production bootstrap requires a separate approved change-control path",))
        if missing:
            return self._blocked(request, BootstrapStatus.BLOCKED_MISSING_HUMAN_DATA.value, tuple(missing))
        steps = self.steps(request)
        status = BootstrapStatus.READY_FOR_REVIEW.value if request.validated_command_evidence_ids else BootstrapStatus.PREVIEW_ONLY.value
        assumptions = ("exact vendor commands are intentionally absent unless validated command evidence is supplied", "console or approved OOB access remains a human-controlled prerequisite")
        return BootstrapArtifact(self._artifact_id(request), status, self.vendor, request.platform, request.device_id, False, False, steps, (), (), assumptions, tuple(dict.fromkeys(request.evidence_ids + request.validated_command_evidence_ids)), tuple(reference for reference in (request.credential_reference, request.oob_reference) if reference), ("bootstrap plan is not a production execution authorization", "vendor command syntax is not fabricated"))

    def steps(self, request: BootstrapRequest) -> tuple[BootstrapStep, ...]:
        """Return common lifecycle intents; subclasses may refine family wording."""
        return (
            BootstrapStep("access", "Establish controlled bootstrap access", "establish local console or approved OOB access", True, False, ("access path identity verified",)),
            BootstrapStep("identity", "Set device identity", "apply human-approved hostname and device identity", True, False, ("identity reconciles with asset record",)),
            BootstrapStep("management", "Establish secure management baseline", "apply secure management transport and management source restrictions", True, False, ("management access remains available", "audit logging remains enabled")),
            BootstrapStep("time_logging", "Establish time and logging prerequisites", "configure approved time synchronization and logging references", True, False, ("time source and logging destination are human supplied",)),
            BootstrapStep("save_verify", "Save and verify bootstrap state", "retain a rollback artifact and collect read-only verification evidence", True, False, ("configuration integrity verified", "rollback artifact retained")),
        )

    def _missing(self, request: BootstrapRequest) -> tuple[str, ...]:
        """Return inputs that cannot be safely inferred."""
        required = [field for field in ("device_id", "vendor", "platform", "endpoint_reference") if not getattr(request, field)]
        if not request.console_available and not request.oob_reference:
            required.append("console_available_or_oob_reference")
        if request.credential_reference and not request.credential_reference.startswith("secret://"):
            required.append("credential_reference_must_be_secret_reference")
        return tuple(required)

    def _blocked(self, request: BootstrapRequest, status: str, reasons: Sequence[str]) -> BootstrapArtifact:
        """Create a non-executable blocked artifact."""
        return BootstrapArtifact(self._artifact_id(request), status, self.vendor or request.vendor, request.platform, request.device_id, False, False, required_human_inputs=tuple(dict.fromkeys(str(item) for item in reasons)), assumptions=("blocked artifact must not be executed",), evidence_ids=request.evidence_ids, secret_references=tuple(reference for reference in (request.credential_reference, request.oob_reference) if reference))

    @staticmethod
    def _artifact_id(request: BootstrapRequest) -> str:
        """Create a deterministic identifier from non-secret request metadata."""
        return f"bootstrap:{request.vendor.lower()}:{request.device_id}:{request.platform.lower()}"
