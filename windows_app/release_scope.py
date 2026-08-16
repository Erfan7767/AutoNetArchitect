"""Explicit Windows V1 release boundaries for the local agent shell."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PackageTrustState(str, Enum):
    """Trust state for a Windows package before installation."""

    SIGNED = "signed"
    UNSIGNED = "unsigned"
    UNKNOWN = "unknown"


class LocalWorkspacePolicy(BaseModel):
    """Local storage and consent contract for a single-user V1 agent."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace_root: str = Field(min_length=1, max_length=260)
    single_user_only: bool = True
    secrets_stored_locally: bool = False
    explicit_scope_consent_required: bool = True
    read_only_discovery_default: bool = True
    production_execution_enabled: bool = False


class WindowsReleaseScope(BaseModel):
    """V1 distribution statement that does not imply signed production readiness."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    package_trust: PackageTrustState
    installable_shell: bool = True
    local_workspace: LocalWorkspacePolicy
    laboratory_only: bool = True
    production_device_execution: bool = False
    limitations: tuple[str, ...] = Field(min_length=1)

    def can_install(self) -> bool:
        """Allow installation only when package trust is explicitly known or signed."""

        return self.package_trust in {PackageTrustState.SIGNED, PackageTrustState.UNSIGNED}

    def requires_warning(self) -> bool:
        """Require a visible warning for unsigned or unknown package trust."""

        return self.package_trust is not PackageTrustState.SIGNED

    def can_start_discovery(self, consent_recorded: bool) -> bool:
        """Require explicit scope consent before any local discovery starts."""

        return consent_recorded and self.local_workspace.explicit_scope_consent_required


def default_windows_v1_scope(workspace_root: str, package_trust: PackageTrustState) -> WindowsReleaseScope:
    """Return the conservative Windows V1 scope used by the desktop shell."""

    return WindowsReleaseScope(
        package_trust=package_trust,
        local_workspace=LocalWorkspacePolicy(workspace_root=workspace_root),
        limitations=(
            "V1 is a single-user local shell and does not provide multi-user endpoint administration.",
            "Credentials remain references to the protected secret layer and are not stored in the workspace.",
            "Discovery defaults to explicitly authorized read-only scope.",
            "The package is not a substitute for code signing, endpoint security review, or customer change control.",
            "Laboratory validation and human approval remain required before any production change path.",
        ),
    )
