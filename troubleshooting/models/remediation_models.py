"""Pydantic models for remediation and escalation advice."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .diagnostic_enums import EscalationTarget


class RemediationStep(BaseModel):
    """One proposed remediation step with explicit governance requirements."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    description: str
    commands: list[str] = Field(default_factory=list)
    risk_level: str
    requires_change_request: bool = True
    requires_maintenance_window: bool = True
    estimated_fix_time: str = "unknown"
    verification_after_fix: list[str] = Field(default_factory=list)
    remediation_type: str = "planned_fix"
    safety_warnings: list[str] = Field(default_factory=list)
    read_only_preview: bool = True

    def model_post_init(self, __context: Any) -> None:
        """Reject write execution semantics from diagnostic advice."""
        forbidden = ("configure", "set ", "delete ", "remove ", "reload", "restart", "shutdown", "write", "commit")
        if any(any(token in command.lower() for token in forbidden) for command in self.commands):
            raise ValueError("remediation commands are advisory references and must not contain ungoverned write commands")


class RemediationPlan(BaseModel):
    """Ordered remediation advice with explicit non-execution status."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    root_cause: str
    steps: list[RemediationStep] = Field(default_factory=list)
    plan_type: str = "planned_fix"
    execution_allowed: bool = False
    safety_warnings: list[str] = Field(default_factory=list)
    change_management_reference: str | None = None
    assumptions: list[str] = Field(default_factory=list)


class EscalationRecommendation(BaseModel):
    """Escalation decision and package requirements."""

    model_config = ConfigDict(extra="forbid")

    required: bool
    targets: list[EscalationTarget] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    threshold_evaluations: dict[str, bool] = Field(default_factory=dict)
    package_contents: list[str] = Field(default_factory=list)
    urgency: str = "normal"
