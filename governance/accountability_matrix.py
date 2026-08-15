"""Accountability matrix for critical engineering and operational workflows."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from designers.base_designer import BaseDesigner

from .review_classes import ReviewClass


class RiskClass(str, Enum):
    """Risk classes used by sign-off policy."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class DecisionClass(str, Enum):
    """Decision classes that require distinct human accountability."""

    DESIGN = "design_decision"
    SECURITY = "security_decision"
    COMPLIANCE = "compliance_decision"
    EQUIPMENT = "equipment_selection"
    CONFIGURATION = "configuration_generation"
    DEPLOYMENT = "deployment"
    ROLLBACK = "rollback"
    EMERGENCY_CHANGE = "emergency_change"
    WAIVER = "policy_waiver"


class AccountabilityRequirement(BaseModel):
    """One resolved accountability row."""

    model_config = ConfigDict(extra="forbid")

    workflow: str = Field(min_length=1)
    decision_class: DecisionClass
    risk_class: RiskClass
    accountable_owner_role: str = Field(min_length=1)
    required_review_classes: tuple[ReviewClass, ...] = ()
    required_reviewer_roles: tuple[str, ...] = ()
    required_approver_roles: tuple[str, ...] = ()
    execution_authority_roles: tuple[str, ...] = ()
    escalation_path: tuple[str, ...] = ()
    rationale: tuple[str, ...] = ()
    policy_basis: tuple[str, ...] = ()
    review_required: bool = True
    approval_required: bool = True
    execution_authority_required: bool = True

    @property
    def checkpoint_count(self) -> int:
        """Return the number of human checkpoint categories."""
        return len(self.required_review_classes) + len(self.required_approver_roles) + len(self.execution_authority_roles)


class AccountabilityMatrix(BaseDesigner):
    """Resolve accountability requirements without granting implicit authority."""

    def __init__(self) -> None:
        """Initialize the default conservative policy rows."""
        super().__init__("AccountabilityMatrix")
        self._rows = self._default_rows()
        self.record_decision("accountability_policy", "explicit_matrix", "critical paths require named human roles for review, approval, accountability, and execution authority")

    @staticmethod
    def _default_rows() -> tuple[AccountabilityRequirement, ...]:
        """Build default rows for the project lifecycle."""
        return (
            AccountabilityRequirement(workflow="requirements", decision_class=DecisionClass.DESIGN, risk_class=RiskClass.MEDIUM, accountable_owner_role="requirements_owner", required_review_classes=(ReviewClass.TECHNICAL,), required_reviewer_roles=("technical_reviewer",), required_approver_roles=("service_owner",), execution_authority_roles=("project_owner",), escalation_path=("change_manager", "cto_or_it_director"), rationale=("requirements affect all downstream engineering decisions",), policy_basis=("governance.requirements_review",)),
            AccountabilityRequirement(workflow="design", decision_class=DecisionClass.DESIGN, risk_class=RiskClass.HIGH, accountable_owner_role="design_authority", required_review_classes=(ReviewClass.TECHNICAL,), required_reviewer_roles=("technical_reviewer",), required_approver_roles=("service_owner",), execution_authority_roles=("design_authority",), escalation_path=("change_manager", "cto_or_it_director"), rationale=("non-trivial design choices must be technically reviewed",), policy_basis=("governance.design_review",)),
            AccountabilityRequirement(workflow="security", decision_class=DecisionClass.SECURITY, risk_class=RiskClass.HIGH, accountable_owner_role="security_owner", required_review_classes=(ReviewClass.TECHNICAL, ReviewClass.SECURITY), required_reviewer_roles=("technical_reviewer", "security_reviewer"), required_approver_roles=("security_owner",), execution_authority_roles=("security_owner",), escalation_path=("cto_or_it_director",), rationale=("security-impacting decisions require independent security review",), policy_basis=("governance.security_review",)),
            AccountabilityRequirement(workflow="compliance", decision_class=DecisionClass.COMPLIANCE, risk_class=RiskClass.HIGH, accountable_owner_role="compliance_owner", required_review_classes=(ReviewClass.TECHNICAL, ReviewClass.COMPLIANCE), required_reviewer_roles=("technical_reviewer", "compliance_reviewer"), required_approver_roles=("compliance_owner",), execution_authority_roles=("compliance_owner",), escalation_path=("legal_counsel", "cto_or_it_director"), rationale=("technical compliance scope must be reviewed without claiming certification",), policy_basis=("governance.compliance_review",)),
            AccountabilityRequirement(workflow="configuration", decision_class=DecisionClass.CONFIGURATION, risk_class=RiskClass.MEDIUM, accountable_owner_role="configuration_owner", required_review_classes=(ReviewClass.TECHNICAL,), required_reviewer_roles=("technical_reviewer",), required_approver_roles=("change_manager",), execution_authority_roles=("configuration_operator",), escalation_path=("service_owner",), rationale=("generated configuration requires review before deployment",), policy_basis=("governance.configuration_review",)),
            AccountabilityRequirement(workflow="deployment", decision_class=DecisionClass.DEPLOYMENT, risk_class=RiskClass.CRITICAL, accountable_owner_role="deployment_owner", required_review_classes=(ReviewClass.TECHNICAL, ReviewClass.SECURITY, ReviewClass.DEPLOYMENT_APPROVAL), required_reviewer_roles=("technical_reviewer", "security_reviewer"), required_approver_roles=("deployment_approver", "service_owner"), execution_authority_roles=("deployment_operator",), escalation_path=("change_manager", "cto_or_it_director"), rationale=("production deployment has execution impact and must not rely on a boolean approval alone",), policy_basis=("governance.deployment_signoff",)),
            AccountabilityRequirement(workflow="rollback", decision_class=DecisionClass.ROLLBACK, risk_class=RiskClass.HIGH, accountable_owner_role="rollback_owner", required_review_classes=(ReviewClass.TECHNICAL, ReviewClass.DEPLOYMENT_APPROVAL), required_reviewer_roles=("technical_reviewer",), required_approver_roles=("deployment_approver",), execution_authority_roles=("deployment_operator",), escalation_path=("service_owner", "cto_or_it_director"), rationale=("rollback can be disruptive and requires a named authority",), policy_basis=("governance.rollback_signoff",)),
            AccountabilityRequirement(workflow="emergency_change", decision_class=DecisionClass.EMERGENCY_CHANGE, risk_class=RiskClass.EMERGENCY, accountable_owner_role="emergency_change_owner", required_review_classes=(ReviewClass.EMERGENCY,), required_reviewer_roles=("on_call_manager",), required_approver_roles=("on_call_manager",), execution_authority_roles=("emergency_operator",), escalation_path=("incident_commander", "service_owner", "cto_or_it_director"), rationale=("emergency authority is narrow, time-bound, and audited",), policy_basis=("governance.emergency_change",)),
            AccountabilityRequirement(workflow="waiver", decision_class=DecisionClass.WAIVER, risk_class=RiskClass.HIGH, accountable_owner_role="risk_owner", required_review_classes=(ReviewClass.TECHNICAL, ReviewClass.SECURITY), required_reviewer_roles=("technical_reviewer", "security_reviewer"), required_approver_roles=("risk_owner", "service_owner"), execution_authority_roles=(), escalation_path=("cto_or_it_director", "legal_counsel"), rationale=("waivers do not create execution authority and must expire",), policy_basis=("governance.exception_waiver",), execution_authority_required=False),
        )

    def resolve(self, *, workflow: str, decision_class: DecisionClass | str, risk_class: RiskClass | str, sector: str = "general", clinical_sensitive: bool = False) -> AccountabilityRequirement:
        """Resolve a row and apply bounded sector-specific review additions."""
        selected_decision = DecisionClass(decision_class)
        selected_risk = RiskClass(risk_class)
        row = next((item for item in self._rows if item.workflow == workflow and item.decision_class == selected_decision), None)
        if row is None:
            self.record_assumption("unmapped_workflow", workflow, "workflow was not found in the default matrix and requires human policy mapping")
            return AccountabilityRequirement(workflow=workflow, decision_class=selected_decision, risk_class=selected_risk, accountable_owner_role="human_policy_owner", required_review_classes=(ReviewClass.TECHNICAL,), required_reviewer_roles=("technical_reviewer",), required_approver_roles=("policy_owner",), execution_authority_roles=(), escalation_path=("cto_or_it_director",), rationale=("unmapped workflows are blocked until a human policy owner maps them",), policy_basis=("governance.unmapped_workflow_block",), execution_authority_required=False)
        required_reviews = list(row.required_review_classes)
        reviewer_roles = list(row.required_reviewer_roles)
        approver_roles = list(row.required_approver_roles)
        rationale = list(row.rationale)
        if sector.lower() == "banking" and ReviewClass.SECURITY not in required_reviews and selected_risk in {RiskClass.HIGH, RiskClass.CRITICAL, RiskClass.EMERGENCY}:
            required_reviews.append(ReviewClass.SECURITY)
            reviewer_roles.append("security_reviewer")
            rationale.append("banking sector policy adds security review for elevated risk")
        if sector.lower() in {"hospital", "hospital_clinical", "clinical"} and clinical_sensitive and ReviewClass.COMPLIANCE not in required_reviews:
            required_reviews.append(ReviewClass.COMPLIANCE)
            reviewer_roles.append("clinical_impact_reviewer")
            rationale.append("clinical-sensitive path requires an additional human impact review")
        return row.model_copy(update={"risk_class": selected_risk, "required_review_classes": tuple(dict.fromkeys(required_reviews)), "required_reviewer_roles": tuple(dict.fromkeys(reviewer_roles)), "required_approver_roles": tuple(dict.fromkeys(approver_roles)), "rationale": tuple(dict.fromkeys(rationale))})

    def rows(self) -> tuple[AccountabilityRequirement, ...]:
        """Return default matrix rows."""
        return self._rows
