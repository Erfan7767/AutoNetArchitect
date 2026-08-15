"""Dependency-aware revalidation after expert intervention."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Mapping

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .override_models import OverrideApplication, OverrideTargetType, RevalidationStatus


class RevalidationTrigger(BaseModel):
    """One downstream artifact revalidation obligation."""

    model_config = ConfigDict(extra="forbid")

    trigger_id: str = Field(min_length=1)
    override_id: str = Field(min_length=1)
    artifact_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    affected_workflows: tuple[str, ...] = ()
    required_checkpoints: tuple[str, ...] = ()
    status: RevalidationStatus = RevalidationStatus.REQUIRED
    evidence_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class RevalidationPlan(BaseModel):
    """Plan created after an override."""

    model_config = ConfigDict(extra="forbid")

    override_id: str
    status: RevalidationStatus
    triggers: tuple[RevalidationTrigger, ...] = ()
    reasons: tuple[str, ...] = ()


class RevalidationTriggerEngine(BaseDesigner):
    """Create and close revalidation triggers without claiming completion."""

    def __init__(self) -> None:
        """Initialize trigger registry."""
        super().__init__("RevalidationTriggerEngine")
        self._triggers: dict[str, RevalidationTrigger] = {}
        self.record_decision("revalidation_default", "required_after_dependency_change", "changed decisions trigger downstream verification rather than silently propagating")

    def plan(self, application: OverrideApplication, *, dependency_graph: Mapping[str, Iterable[str]] | None = None) -> RevalidationPlan:
        """Create triggers for affected artifacts and known downstream dependents."""
        if application.revalidation_status == RevalidationStatus.NOT_REQUIRED:
            return RevalidationPlan(override_id=application.override_id, status=RevalidationStatus.NOT_REQUIRED, reasons=("override policy does not require downstream revalidation",))
        graph = dependency_graph or {}
        candidates: list[str] = [application.target_id]
        candidates.extend(application.affected_artifact_ids)
        candidates.extend(str(item) for item in graph.get(application.target_id, ()))
        triggers: list[RevalidationTrigger] = []
        for index, artifact_id in enumerate(dict.fromkeys(candidates)):
            checkpoints = self._checkpoints_for(application.target_type)
            trigger = RevalidationTrigger(trigger_id=f"reval:{application.override_id}:{index}", override_id=application.override_id, artifact_id=artifact_id, reason=f"artifact depends on expert intervention {application.override_id}", affected_workflows=tuple(self._workflows_for(application.target_type)), required_checkpoints=checkpoints, evidence_ids=application.evidence_ids)
            self._triggers[trigger.trigger_id] = trigger
            triggers.append(trigger)
        self.record_decision(f"revalidation:{application.override_id}", RevalidationStatus.REQUIRED.value, "dependent artifacts were converted into explicit revalidation triggers")
        return RevalidationPlan(override_id=application.override_id, status=RevalidationStatus.REQUIRED, triggers=tuple(triggers), reasons=("downstream artifacts require revalidation before production reliance",))

    def complete(self, trigger_id: str, evidence_ids: Iterable[str]) -> RevalidationTrigger:
        """Mark a trigger complete only with explicit verification evidence."""
        evidence = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if not evidence:
            raise ValueError("revalidation completion requires evidence_ids")
        current = self._triggers[trigger_id]
        updated = current.model_copy(update={"status": RevalidationStatus.COMPLETED, "evidence_ids": tuple(dict.fromkeys(current.evidence_ids + evidence)), "completed_at": datetime.now(timezone.utc)})
        self._triggers[trigger_id] = updated
        self.record_decision(f"complete:{trigger_id}", RevalidationStatus.COMPLETED.value, "revalidation completion is accepted only with explicit evidence")
        return updated

    def block(self, trigger_id: str, reason: str) -> RevalidationTrigger:
        """Mark a trigger blocked when revalidation cannot proceed."""
        if not reason.strip():
            raise ValueError("revalidation block reason is mandatory")
        current = self._triggers[trigger_id]
        updated = current.model_copy(update={"status": RevalidationStatus.BLOCKED, "reason": f"{current.reason}; {reason}"})
        self._triggers[trigger_id] = updated
        self.record_decision(f"block:{trigger_id}", RevalidationStatus.BLOCKED.value, reason)
        return updated

    def triggers(self) -> tuple[RevalidationTrigger, ...]:
        """Return all triggers in stable order."""
        return tuple(self._triggers[key] for key in sorted(self._triggers))

    @staticmethod
    def _checkpoints_for(target_type: OverrideTargetType) -> tuple[str, ...]:
        """Map target type to downstream supervised checkpoints."""
        mapping = {OverrideTargetType.REQUIREMENT: ("requirements.analysis_review", "design.intent_review"), OverrideTargetType.DESIGN_DECISION: ("design.intent_review", "design.production_approval"), OverrideTargetType.EQUIPMENT_SELECTION: ("equipment.selection_review", "config.generation_review"), OverrideTargetType.CONFIG_ARTIFACT: ("config.generation_review", "deployment.preparation_gate"), OverrideTargetType.DEPLOYMENT_GATE: ("deployment.execution_gate",), OverrideTargetType.OPERATIONAL_POLICY: ("operations.remediation_gate", "reports.content_review")}
        return mapping[target_type]

    @staticmethod
    def _workflows_for(target_type: OverrideTargetType) -> tuple[str, ...]:
        """Map target type to downstream workflow names."""
        mapping = {OverrideTargetType.REQUIREMENT: ("requirements", "design"), OverrideTargetType.DESIGN_DECISION: ("design", "equipment", "config_generation"), OverrideTargetType.EQUIPMENT_SELECTION: ("equipment", "config_generation", "deployment_preparation"), OverrideTargetType.CONFIG_ARTIFACT: ("config_generation", "deployment_preparation", "deployment_execution"), OverrideTargetType.DEPLOYMENT_GATE: ("deployment_execution",), OverrideTargetType.OPERATIONAL_POLICY: ("operations", "reports")}
        return mapping[target_type]
