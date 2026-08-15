"""Core typed contracts for governed network change management."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Mapping


class ChangeType(str, Enum):
    """Lifecycle class for a change request."""

    STANDARD = "standard"
    NORMAL = "normal"
    EMERGENCY = "emergency"


class ChangeCategory(str, Enum):
    """Technical category of a change."""

    CONFIGURATION = "configuration"
    HARDWARE = "hardware"
    SOFTWARE = "software"
    CONNECTIVITY = "connectivity"
    SECURITY = "security"
    TOPOLOGY = "topology"
    MIGRATION = "migration"
    DECOMMISSION = "decommission"
    NEW_DEPLOYMENT = "new_deployment"


class ChangePriority(str, Enum):
    """Business urgency of a change."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ChangeStatus(str, Enum):
    """Allowed lifecycle statuses."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    RISK_ASSESSED = "risk_assessed"
    IMPACT_ASSESSED = "impact_assessed"
    PLAN_COMPLETE = "plan_complete"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    VERIFICATION = "verification"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class ClosureCode(str, Enum):
    """Closure reason for a completed lifecycle."""

    SUCCESSFUL = "successful"
    SUCCESSFUL_WITH_ISSUES = "successful_with_issues"
    FAILED_ROLLED_BACK = "failed_rolled_back"
    FAILED_PARTIAL = "failed_partial"
    CANCELLED_BY_REQUESTER = "cancelled_by_requester"
    CANCELLED_BY_APPROVER = "cancelled_by_approver"
    SUPERSEDED = "superseded"


class ApprovalDecision(str, Enum):
    """Individual approval decision."""

    APPROVED = "approved"
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    PENDING = "pending"


class StepStatus(str, Enum):
    """Implementation step state."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStatus(str, Enum):
    """Overall execution state."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class VerificationStatus(str, Enum):
    """Verification outcome."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


class ImpactClass(str, Enum):
    """Expected service impact class."""

    NO_IMPACT = "no_impact"
    MINOR_IMPACT = "minor_impact"
    MODERATE_IMPACT = "moderate_impact"
    MAJOR_IMPACT = "major_impact"
    SERVICE_OUTAGE = "service_outage"


class RiskLevel(str, Enum):
    """Weighted risk level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RollbackStrategy(str, Enum):
    """Supported rollback strategies."""

    FULL_ROLLBACK = "full_rollback"
    PARTIAL_ROLLBACK = "partial_rollback"
    FORWARD_FIX = "forward_fix"
    RESTORE_FROM_BACKUP = "restore_from_backup"


class RollbackTrigger(str, Enum):
    """Rollback trigger classes."""

    EXPLICIT_HUMAN = "explicit_human"
    AUTOMATIC_CRITERIA = "automatic_criteria"
    TIMEOUT = "timeout"


class FreezeType(str, Enum):
    """Change freeze modes."""

    FULL_FREEZE = "full_freeze"
    PARTIAL_FREEZE = "partial_freeze"
    SOFT_FREEZE = "soft_freeze"


@dataclass(frozen=True)
class DeviceRef:
    """Reference to a device without embedding credentials."""

    device_id: str
    device_name: str = ""
    vendor: str = ""
    platform: str = ""
    site_id: str = ""
    core_infrastructure: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize the device reference."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ServiceRef:
    """Reference to an affected service."""

    service_id: str
    service_name: str = ""
    criticality: str = "normal"
    owner: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the service reference."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class SiteRef:
    """Reference to an affected site."""

    site_id: str
    site_name: str = ""
    region: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize the site reference."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ConfigChange:
    """Before/after configuration section with safe command references."""

    device_id: str
    device_name: str
    change_section: str
    before_config: str = ""
    after_config: str = ""
    diff: str = ""
    commands_to_apply: tuple[str, ...] = ()
    commands_to_rollback: tuple[str, ...] = ()
    source_artifact_id: str = ""
    validator_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration change data."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ImplementationStep:
    """One ordered implementation step."""

    step_number: int
    description: str
    device: str
    commands: tuple[str, ...] = ()
    expected_result: str = ""
    verification_command: str = ""
    verification_expected_output: str = ""
    estimated_duration: timedelta = timedelta(0)
    rollback_commands: tuple[str, ...] = ()
    can_proceed_on_failure: bool = False
    human_verification_required: bool = True
    go_no_go_criteria: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize an implementation step."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ImplementationPlan:
    """Ordered change execution plan."""

    steps: tuple[ImplementationStep, ...] = ()
    estimated_duration: timedelta = timedelta(0)
    maintenance_window_required: bool = True
    service_impact_during_change: str = ImpactClass.NO_IMPACT.value
    parallel_vs_sequential: str = "sequential"
    prerequisites: tuple[str, ...] = ()
    validator_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize implementation plan."""
        return _clean({"steps": [step.to_dict() for step in self.steps], "estimated_duration": self.estimated_duration, "maintenance_window_required": self.maintenance_window_required, "service_impact_during_change": self.service_impact_during_change, "parallel_vs_sequential": self.parallel_vs_sequential, "prerequisites": self.prerequisites, "validator_evidence_ids": self.validator_evidence_ids})


@dataclass(frozen=True)
class RollbackStep:
    """One ordered rollback step."""

    step_number: int
    description: str
    device: str
    commands: tuple[str, ...] = ()
    expected_result: str = ""
    verification_command: str = ""
    verification_expected_output: str = ""
    estimated_duration: timedelta = timedelta(0)

    def to_dict(self) -> dict[str, Any]:
        """Serialize rollback step."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class RollbackPlan:
    """Rollback strategy and safety conditions."""

    strategy: str = RollbackStrategy.FULL_ROLLBACK.value
    steps: tuple[RollbackStep, ...] = ()
    estimated_duration: timedelta = timedelta(0)
    rollback_trigger_criteria: tuple[str, ...] = ()
    point_of_no_return: int | None = None
    partial_rollback_possible: bool = True
    backup_required: bool = True
    backup_evidence_ids: tuple[str, ...] = ()
    safety_policies_preserved: tuple[str, ...] = ("management_access", "authentication", "audit_logging", "segmentation")

    def to_dict(self) -> dict[str, Any]:
        """Serialize rollback plan."""
        return _clean({"strategy": self.strategy, "steps": [step.to_dict() for step in self.steps], "estimated_duration": self.estimated_duration, "rollback_trigger_criteria": self.rollback_trigger_criteria, "point_of_no_return": self.point_of_no_return, "partial_rollback_possible": self.partial_rollback_possible, "backup_required": self.backup_required, "backup_evidence_ids": self.backup_evidence_ids, "safety_policies_preserved": self.safety_policies_preserved})


@dataclass(frozen=True)
class TestPlan:
    """Pre- and post-change validation plan."""

    lab_tested: bool = False
    lab_evidence_ids: tuple[str, ...] = ()
    checks: tuple[str, ...] = ()
    required_verification_types: tuple[str, ...] = ()
    user_confirmation_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize test plan."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class RiskAssessment:
    """Weighted change risk assessment."""

    score: float = 0.0
    risk_level: str = RiskLevel.LOW.value
    factors: dict[str, int] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)
    mitigations: tuple[str, ...] = ()
    rationale: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize risk assessment."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ImpactAssessment:
    """Direct and indirect impact analysis."""

    direct_device_ids: tuple[str, ...] = ()
    indirect_device_ids: tuple[str, ...] = ()
    affected_service_ids: tuple[str, ...] = ()
    affected_user_count: int | None = None
    affected_site_ids: tuple[str, ...] = ()
    expected_downtime: timedelta = timedelta(0)
    performance_degradation_window: timedelta = timedelta(0)
    impact_class: str = ImpactClass.NO_IMPACT.value
    rationale: str = ""
    dependency_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize impact assessment."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class Approval:
    """One approval decision with optional conditions."""

    approver_role: str
    approver_name: str = ""
    decision: str = ApprovalDecision.PENDING.value
    decision_reason: str = ""
    decided_at: datetime | None = None
    conditions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize approval."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class MaintenanceWindow:
    """Requested maintenance window."""

    start_time: datetime
    end_time: datetime
    timezone: str
    business_justification: str
    affected_users_notified: bool = False
    notification_sent_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize maintenance window."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class ExecutionEvent:
    """Immutable execution event for a step."""

    event_id: str
    step_number: int
    step_status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    executed_by: str = ""
    actual_output: str = ""
    matches_expected: bool | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize execution event."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class VerificationResult:
    """One post-change verification result."""

    verification_id: str
    verification_type: str
    command_or_action: str
    expected_result: str
    actual_result: str = ""
    status: str = VerificationStatus.NOT_VERIFIABLE.value
    executed_at: datetime | None = None
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize verification result."""
        return _clean(asdict(self))


@dataclass(frozen=True)
class VerificationResults:
    """Aggregate verification results."""

    results: tuple[VerificationResult, ...] = ()
    overall_status: str = VerificationStatus.NOT_VERIFIABLE.value
    rollback_consideration_required: bool = False
    post_implementation_review_required: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize verification results."""
        return _clean({"results": [result.to_dict() for result in self.results], "overall_status": self.overall_status, "rollback_consideration_required": self.rollback_consideration_required, "post_implementation_review_required": self.post_implementation_review_required})


@dataclass
class ChangeRequest:
    """Mutable V1 local change request with embedded evidence and decisions."""

    change_id: str
    title: str
    description: str
    requester: str
    change_type: str = ChangeType.NORMAL.value
    change_category: str = ChangeCategory.CONFIGURATION.value
    priority: str = ChangePriority.MEDIUM.value
    status: str = ChangeStatus.DRAFT.value
    affected_devices: list[DeviceRef] = field(default_factory=list)
    affected_services: list[ServiceRef] = field(default_factory=list)
    affected_sites: list[SiteRef] = field(default_factory=list)
    related_project: str = ""
    config_changes: list[ConfigChange] = field(default_factory=list)
    implementation_plan: ImplementationPlan = field(default_factory=ImplementationPlan)
    rollback_plan: RollbackPlan = field(default_factory=RollbackPlan)
    test_plan: TestPlan = field(default_factory=TestPlan)
    risk_assessment: RiskAssessment = field(default_factory=RiskAssessment)
    impact_assessment: ImpactAssessment = field(default_factory=ImpactAssessment)
    approvals: list[Approval] = field(default_factory=list)
    scheduled_window: MaintenanceWindow | None = None
    execution_log: list[ExecutionEvent] = field(default_factory=list)
    verification_results: VerificationResults = field(default_factory=VerificationResults)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    closed_at: datetime | None = None
    closure_code: str | None = None
    lessons_learned: str = ""
    decision_records: list[Any] = field(default_factory=list)
    assumptions: list[Any] = field(default_factory=list)
    history_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize a request recursively."""
        return _clean({"change_id": self.change_id, "title": self.title, "description": self.description, "requester": self.requester, "change_type": self.change_type, "change_category": self.change_category, "priority": self.priority, "status": self.status, "affected_devices": [item.to_dict() for item in self.affected_devices], "affected_services": [item.to_dict() for item in self.affected_services], "affected_sites": [item.to_dict() for item in self.affected_sites], "related_project": self.related_project, "config_changes": [item.to_dict() for item in self.config_changes], "implementation_plan": self.implementation_plan.to_dict(), "rollback_plan": self.rollback_plan.to_dict(), "test_plan": self.test_plan.to_dict(), "risk_assessment": self.risk_assessment.to_dict(), "impact_assessment": self.impact_assessment.to_dict(), "approvals": [item.to_dict() for item in self.approvals], "scheduled_window": self.scheduled_window.to_dict() if self.scheduled_window else None, "execution_log": [item.to_dict() for item in self.execution_log], "verification_results": self.verification_results.to_dict(), "created_at": self.created_at, "updated_at": self.updated_at, "closed_at": self.closed_at, "closure_code": self.closure_code, "lessons_learned": self.lessons_learned, "decision_records": [getattr(item, "__dict__", item) for item in self.decision_records], "assumptions": [getattr(item, "__dict__", item) for item in self.assumptions], "history_ids": self.history_ids})


@dataclass(frozen=True)
class ChangeLifecycle:
    """Lifecycle artifact emitted by the orchestrator."""

    change_id: str
    current_status: str
    completed_steps: tuple[str, ...]
    next_steps: tuple[str, ...]
    prerequisites_satisfied: bool
    decision_ids: tuple[str, ...] = ()
    assumption_keys: tuple[str, ...] = ()
    history_ids: tuple[str, ...] = ()
    production_execution_allowed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize lifecycle artifact."""
        return _clean(asdict(self))


def _clean(value: Any) -> Any:
    """Convert enums, datetimes, timedeltas, and nested values to JSON-safe data."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, Mapping):
        return {str(key): _clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_clean(item) for item in value]
    if hasattr(value, "to_dict"):
        return _clean(value.to_dict())
    return value
