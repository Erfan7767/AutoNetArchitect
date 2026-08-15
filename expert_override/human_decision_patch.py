"""Conflict-checked human decision patches."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner
from execution_protocol.diff_patch_manager import DiffPatchManager


class HumanDecisionPatch(BaseModel):
    """Explicit patch from a human decision to a proposed artifact value."""

    model_config = ConfigDict(extra="forbid")

    patch_id: str = Field(min_length=1)
    target_id: str = Field(min_length=1)
    author_id: str = Field(min_length=1)
    author_role: str = Field(min_length=1)
    base_value: Any
    proposed_value: Any
    reason: str = Field(min_length=1)
    changed_paths: tuple[str, ...] = ()
    override_id: str = ""


class PatchResult(BaseModel):
    """Result of applying or rejecting a human patch."""

    model_config = ConfigDict(extra="forbid")

    patch_id: str
    target_id: str
    applied: bool
    resulting_value: Any
    conflict: bool = False
    reasons: tuple[str, ...] = ()
    diff: str = ""
    provenance: tuple[str, ...] = ()


class HumanDecisionPatchManager(BaseDesigner):
    """Apply human patches only when the supplied base still matches."""

    def __init__(self) -> None:
        """Initialize patch manager with deterministic diff utility."""
        super().__init__("HumanDecisionPatchManager")
        self.diff_manager = DiffPatchManager()
        self.record_decision("patch_policy", "exact_base_match_required", "human decision patches cannot silently replace a changed artifact")

    def apply(self, patch: HumanDecisionPatch, current_value: Any) -> PatchResult:
        """Apply a conflict-checked patch and return explicit provenance."""
        if current_value != patch.base_value:
            result = PatchResult(patch_id=patch.patch_id, target_id=patch.target_id, applied=False, resulting_value=current_value, conflict=True, reasons=("current artifact differs from patch base",), provenance=(patch.patch_id, patch.override_id) if patch.override_id else (patch.patch_id,))
            self.record_decision(f"patch:{patch.patch_id}", "conflict", "human patch was refused because the artifact changed after the patch base")
            return result
        diff = ""
        if isinstance(patch.base_value, str) and isinstance(patch.proposed_value, str):
            diff = self.diff_manager.create_diff(patch.base_value, patch.proposed_value, patch.target_id)
        result = PatchResult(patch_id=patch.patch_id, target_id=patch.target_id, applied=True, resulting_value=patch.proposed_value, diff=diff, provenance=(patch.patch_id, patch.override_id) if patch.override_id else (patch.patch_id,))
        self.record_decision(f"patch:{patch.patch_id}", "applied", "human patch was applied only after exact base verification")
        return result
