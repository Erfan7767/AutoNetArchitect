"""Pydantic v2 contracts for the AutoNetArchitect Incident Response Engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentSeverity(str, Enum):
    """Operational severity with response and update policy."""

    P1_CRITICAL = "P1"
    P2_HIGH = "P2"
    P3_MEDIUM = "P3"
    P4_LOW = "P4"


class IncidentPriority(str, Enum):
    """Incident handling priority."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IncidentCategory(str, Enum):
    """Root category of an incident."""

    NETWORK_OUTAGE = "network_outage"
    NETWORK_DEGRADATION = "network_degradation"
    SECURITY_INCIDENT = "security_incident"
    HARDWARE_FAILURE = "hardware_failure"
    SOFTWARE_BUG = "software_bug"
    CONFIGURATION_ERROR = "configuration_error"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    EXTERNAL_DEPENDENCY = "external_dependency"
    PLANNED_MAINTENANCE_ISSUE = "planned_maintenance_issue"
    ENVIRONMENTAL = "environmental"


class IncidentStatus(str, Enum):
    """Incident lifecycle states."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    CONTAINMENT = "containment"
    CONTAINED = "contained"
    ERADICATING = "eradicating"
    RECOVERING = "recovering"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class DetectionMethod(str, Enum):
    """How an incident was detected."""

    MONITORING = "monitoring"
    USER = "user"
    ENGINEER = "engineer"
    AUTOMATED_RULE = "automated_rule"
    EXTERNAL_NOTIFICATION = "external_notification"


class IncidentPhase(str, Enum):
    """Orchestrated lifecycle phases."""

    DETECTION = "detection"
    LOGGING = "logging"
    CLASSIFICATION = "classification"
    NOTIFICATION = "notification"
    DIAGNOSIS = "diagnosis"
    CONTAINMENT = "containment"
    ERADICATION = "eradication"
    RECOVERY = "recovery"
    VERIFICATION = "verification"
    CLOSURE = "closure"
    POST_INCIDENT_REVIEW = "post_incident_review"


class SLAStatus(str, Enum):
    """SLA state."""

    NOT_STARTED = "not_started"
    MET = "met"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    ONGOING = "ongoing"


class ContainmentPlan(BaseModel):
    """Human-approved containment proposal; never an execution command."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    strategy: str
    steps: list["IncidentPlanStep"] = Field(default_factory=list)
    preserves_evidence: bool = True
    wider_outage_risk: str = "unknown"
    execution_allowed: bool = False
    approval_reference: str | None = None
    assumptions: list[str] = Field(default_factory=list)


class EradicationPlan(BaseModel):
    """Root-cause removal proposal linked to change governance."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    root_cause: str
    remediation_type: str
    steps: list["IncidentPlanStep"] = Field(default_factory=list)
    change_request_reference: str | None = None
    vendor_case_reference: str | None = None
    firmware_reference: str | None = None
    execution_allowed: bool = False
    assumptions: list[str] = Field(default_factory=list)


class RecoveryPlan(BaseModel):
    """Ordered service recovery plan."""

    model_config = ConfigDict(extra="forbid")

    plan_id: str
    mode: str
    services: list["RecoveryServiceStep"] = Field(default_factory=list)
    verification_criteria: list[str] = Field(default_factory=list)
    monitoring_confirmation_required: bool = True
    user_confirmation_required: bool = False
    execution_allowed: bool = False
    assumptions: list[str] = Field(default_factory=list)


class IncidentPlanStep(BaseModel):
    """One read-only proposal step for containment or eradication."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    action: str
    commands: list[str] = Field(default_factory=list)
    risk: str
    requires_approval: bool = True
    estimated_time: timedelta | None = None
    verification: str
    reversible: bool = False
    backup_required: bool = True
    evidence_preservation_required: bool = False

    def model_post_init(self, __context: Any) -> None:
        """Enforce human approval and reject obvious write execution in V1."""
        if not self.requires_approval:
            raise ValueError("all containment and eradication steps require human approval in V1")
        forbidden = ("configure", "conf t", "set ", "delete ", "remove ", "reload", "restart", "shutdown", "write", "commit")
        if any(any(token in command.lower() for token in forbidden) for command in self.commands):
            raise ValueError("incident plans may contain command references only when they remain governed and non-executing")


class RecoveryServiceStep(BaseModel):
    """One service recovery item."""

    model_config = ConfigDict(extra="forbid")

    service_id: str
    recovery_action: str
    verification_criteria: list[str] = Field(default_factory=list)
    estimated_time: timedelta | None = None
    dependencies: list[str] = Field(default_factory=list)
    priority_order: int = 0
    confirmation_source: str = "monitoring_or_human_required"


class BusinessImpact(BaseModel):
    """Explicit or unknown business impact values."""

    model_config = ConfigDict(extra="forbid")

    revenue_impact: str = "unknown"
    operational_impact: str = "unknown"
    reputation_impact: str = "unknown"
    compliance_impact: str = "unknown"
    regulatory_notification_required: bool | None = None
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate confidence."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("business impact confidence must be between zero and one")


class ImpactAssessment(BaseModel):
    """Technical and business blast-radius assessment."""

    model_config = ConfigDict(extra="forbid")

    affected_devices: list[str] = Field(default_factory=list)
    affected_services: list[str] = Field(default_factory=list)
    affected_users_estimate: int | None = None
    affected_sites: list[str] = Field(default_factory=list)
    business_impact: BusinessImpact
    blast_radius: str = "unknown"
    dependencies_considered: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    assumptions: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate counts and confidence."""
        if self.affected_users_estimate is not None and self.affected_users_estimate < 0:
            raise ValueError("affected users estimate cannot be negative")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("impact assessment confidence must be between zero and one")


class TimelineEntry(BaseModel):
    """Immutable incident timeline entry."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: str
    description: str
    performed_by: str
    evidence: list[str] = Field(default_factory=list)
    automated: bool = False


class Communication(BaseModel):
    """Generated communication artifact, not a sent message."""

    model_config = ConfigDict(extra="forbid")

    communication_id: str
    communication_type: str
    audience: str
    channel: str
    language: str
    subject: str
    body: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    sent: bool = False
    sent_reference: str | None = None


class Lesson(BaseModel):
    """Blame-free learning item."""

    model_config = ConfigDict(extra="forbid")

    lesson_id: str
    lesson_type: str
    statement: str
    action_owner: str = ""
    due_date: datetime | None = None
    related_change_reference: str | None = None
    knowledge_update_reference: str | None = None


class Incident(BaseModel):
    """Complete incident record."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str = Field(pattern=r"^INC-\d{8}-\d{4}$")
    title: str
    description: str
    status: IncidentStatus = IncidentStatus.NEW
    severity: IncidentSeverity
    priority: IncidentPriority
    category: IncidentCategory
    affected_services: list[str] = Field(default_factory=list)
    affected_devices: list[str] = Field(default_factory=list)
    affected_sites: list[str] = Field(default_factory=list)
    affected_users_estimate: int | None = None
    detected_at: datetime
    detected_by: str
    detection_method: DetectionMethod
    assigned_to: str = ""
    escalation_level: int = 0
    related_changes: list[str] = Field(default_factory=list)
    related_incidents: list[str] = Field(default_factory=list)
    diagnostic_session_id: str | None = None
    containment_plan: ContainmentPlan | None = None
    eradication_plan: EradicationPlan | None = None
    recovery_plan: RecoveryPlan | None = None
    timeline: list[TimelineEntry] = Field(default_factory=list)
    communications: list[Communication] = Field(default_factory=list)
    root_cause: str = ""
    resolution: str = ""
    workaround: str = ""
    lessons_learned: list[Lesson] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: datetime | None = None
    contained_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    mttr: timedelta | None = None
    impact_assessment: ImpactAssessment | None = None
    decision_records: list[Any] = Field(default_factory=list)
    assumptions: list[Any] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate basic incident invariants."""
        if self.affected_users_estimate is not None and self.affected_users_estimate < 0:
            raise ValueError("affected users estimate cannot be negative")
        if self.escalation_level < 0 or self.escalation_level > 4:
            raise ValueError("escalation level must be between zero and four")


class SLAProfile(BaseModel):
    """Severity-specific response, update, and resolution SLAs."""

    model_config = ConfigDict(extra="forbid")

    severity: IncidentSeverity
    response_sla: timedelta
    update_sla: timedelta
    resolution_sla: timedelta
    escalation_after: timedelta


class SLATracking(BaseModel):
    """Current SLA compliance state."""

    model_config = ConfigDict(extra="forbid")

    incident_id: str
    profile: SLAProfile
    response_time: timedelta | None = None
    response_status: SLAStatus = SLAStatus.NOT_STARTED
    resolution_time: timedelta | None = None
    resolution_status: SLAStatus = SLAStatus.ONGOING
    update_due_at: datetime | None = None
    warning_thresholds_reached: list[int] = Field(default_factory=list)
    breach_notifications_required: bool = False
    assumptions: list[str] = Field(default_factory=list)


class IncidentReview(BaseModel):
    """Post-incident review artifact."""

    model_config = ConfigDict(extra="forbid")

    review_id: str
    incident_id: str
    required: bool
    incident_summary: str
    timeline_review: str
    root_cause_analysis: str
    what_went_well: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    detection_effectiveness: str = "unknown"
    response_effectiveness: str = "unknown"
    communication_effectiveness: str = "unknown"
    tool_effectiveness: str = "unknown"
    process_gaps: list[str] = Field(default_factory=list)
    action_items: list["ReviewActionItem"] = Field(default_factory=list)
    knowledge_updates: list[str] = Field(default_factory=list)
    blame_free: bool = True


class ReviewActionItem(BaseModel):
    """Preventive, detective, or corrective follow-up."""

    model_config = ConfigDict(extra="forbid")

    action_id: str
    action_type: str
    description: str
    owner: str
    due_date: datetime | None = None
    related_change_reference: str | None = None


class RunbookStep(BaseModel):
    """One runbook step tracked for human execution."""

    model_config = ConfigDict(extra="forbid")

    step_id: str
    order: int
    description: str
    commands: list[str] = Field(default_factory=list)
    expected_result: str = ""
    failure_branch: str | None = None
    status: str = "not_started"
    result: str = ""
    executed_by: str = ""
    executed_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        """Reject ungoverned destructive commands from runbook artifacts."""
        forbidden = ("reload", "restart", "shutdown", "delete ", "remove ", "write", "commit")
        if any(any(token in command.lower() for token in forbidden) for command in self.commands):
            raise ValueError("runbook commands must be reviewed before being displayed to a human operator")


class IncidentRunbook(BaseModel):
    """Runbook loaded from a validated local data asset."""

    model_config = ConfigDict(extra="forbid")

    runbook_id: str
    incident_category: IncidentCategory
    title: str
    version: str
    steps: list[RunbookStep] = Field(default_factory=list)
    requires_incident_commander: bool = True
    evidence_preservation_notes: list[str] = Field(default_factory=list)
