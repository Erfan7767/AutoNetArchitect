"""First-class workflow mode and checkpoint decision taxonomy."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner


class WorkflowMode(str, Enum):
    """Supported execution modes for workflow orchestration."""

    SUPERVISED = "supervised"
    PREVIEW = "preview"
    READ_ONLY = "read_only"


class SupervisionDecision(str, Enum):
    """Decision returned by every supervision checkpoint."""

    AUTO_CONTINUE = "auto-continue"
    REQUIRES_REVIEW = "requires-review"
    REQUIRES_APPROVAL = "requires-approval"
    BLOCKED = "blocked"


class WorkflowStage(str, Enum):
    """Lifecycle stages covered by supervised mode."""

    QUESTIONNAIRE = "questionnaire"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    EQUIPMENT = "equipment"
    CONFIG_GENERATION = "config_generation"
    DEPLOYMENT_PREPARATION = "deployment_preparation"
    DEPLOYMENT_EXECUTION = "deployment_execution"
    OPERATIONS = "operations"
    COMPLIANCE = "compliance"
    REPORTS = "reports"


class WorkflowModeState(BaseModel):
    """Explicit mode state carried by an orchestrator."""

    model_config = ConfigDict(extra="forbid")

    mode: WorkflowMode = WorkflowMode.SUPERVISED
    high_assurance: bool = True
    autonomy_permitted: bool = False
    human_owner_id: str | None = None
    human_owner_role: str = "engineer_in_charge"
    rationale: str = "supervised mode is the default high-assurance path"

    def allows_mutation(self) -> bool:
        """Return whether a mutating operation may be considered by later gates."""
        return self.mode == WorkflowMode.SUPERVISED and self.human_owner_id is not None


class WorkflowModeManager(BaseDesigner):
    """Create and validate explicit workflow mode state."""

    def __init__(self) -> None:
        """Initialize mode manager with deny-by-default autonomy semantics."""
        super().__init__("WorkflowModeManager")
        self.record_decision("default_workflow_mode", WorkflowMode.SUPERVISED.value, "high-assurance workflows begin under human supervision and do not infer autonomy")

    def create(self, *, mode: WorkflowMode | str = WorkflowMode.SUPERVISED, human_owner_id: str | None = None, human_owner_role: str = "engineer_in_charge", high_assurance: bool = True) -> WorkflowModeState:
        """Create a state and keep autonomy disabled for every supported mode."""
        selected = WorkflowMode(mode)
        if selected == WorkflowMode.SUPERVISED and high_assurance and not human_owner_id:
            self.record_assumption("human_owner_id", "not supplied", "a human owner is required before a mutating supervised action can proceed")
        state = WorkflowModeState(mode=selected, high_assurance=high_assurance, autonomy_permitted=False, human_owner_id=human_owner_id, human_owner_role=human_owner_role)
        self.record_decision(f"mode:{selected.value}", state.model_dump(mode="json"), "mode is explicit and never escalates to autonomous execution")
        return state
