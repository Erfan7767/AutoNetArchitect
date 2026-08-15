"""Governed end-to-end incident lifecycle orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord

from ._common import assumption_dict, decision_dict, make_assumption, make_decision
from .auto_detection_rules import AutoDetectionRules, DetectionResult
from .communication_manager import CommunicationManager
from .containment_planner import ContainmentPlanner
from .eradication_planner import EradicationPlanner
from .escalation_engine import EscalationDecision, EscalationEngine
from .impact_assessor import ImpactAssessor
from .integration_adapters import IncidentIntegrationAdapters
from .incident_manager import IncidentManager
from .incident_models import Communication, ContainmentPlan, DetectionMethod, EradicationPlan, Incident, IncidentCategory, IncidentPriority, IncidentReview, IncidentSeverity, IncidentStatus, RecoveryPlan, TimelineEntry
from .post_incident_reviewer import PostIncidentReviewer
from .recovery_planner import RecoveryPlanner
from .severity_classifier import SeverityClassification, SeverityClassifier
from .sla_tracker import SLATracker, SLATracking
from .timeline_recorder import TimelineRecorder
from .war_room_coordinator import WarRoomArtifact, WarRoomCoordinator


class IncidentOrchestrator:
    """Coordinate all incident stages without automatic network containment or remediation."""

    def __init__(self, *, audit_trail: AuditTrail | None = None, troubleshooting_orchestrator: Any | None = None, incident_manager: IncidentManager | None = None, integrations: IncidentIntegrationAdapters | None = None) -> None:
        """Initialize incident services and optional cross-layer adapters."""
        self.audit_trail = audit_trail
        self.integrations = integrations or IncidentIntegrationAdapters()
        self.manager = incident_manager or IncidentManager(audit_trail=audit_trail)
        self.troubleshooting_orchestrator = troubleshooting_orchestrator
        self.severity_classifier = SeverityClassifier()
        self.impact_assessor = ImpactAssessor()
        self.containment_planner = ContainmentPlanner()
        self.eradication_planner = EradicationPlanner()
        self.recovery_planner = RecoveryPlanner()
        self.escalation_engine = EscalationEngine()
        self.communication_manager = CommunicationManager()
        self.timeline_recorder = TimelineRecorder(audit_trail=audit_trail)
        self.war_room_coordinator = WarRoomCoordinator()
        self.sla_tracker = SLATracker()
        self.post_incident_reviewer = PostIncidentReviewer()
        self.auto_detection_rules = AutoDetectionRules()
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def detect(self, *, title: str, description: str, detected_by: str, detection_method: DetectionMethod, affected_users: int | None, service_criticality: str, business_impact: str, category: IncidentCategory, affected_services: Sequence[str] = (), affected_devices: Sequence[str] = (), affected_sites: Sequence[str] = (), sector: str = "", business_hours: bool | None = None, workaround_available: bool | None = None, duration_expected_minutes: int | None = None, human_severity_override: IncidentSeverity | str | None = None) -> Incident:
        """Detect and log an incident after explicit severity classification."""
        classification = self.severity_classifier.classify(affected_users=affected_users, service_criticality=service_criticality, business_impact=business_impact, business_hours=business_hours, workaround_available=workaround_available, duration_expected_minutes=duration_expected_minutes, sector=sector, human_override=human_severity_override)
        incident = self.manager.create(title=title, description=description, severity=classification.severity, priority=classification.priority, category=category, detected_by=detected_by, detection_method=detection_method, affected_services=list(affected_services), affected_devices=list(affected_devices), affected_sites=list(affected_sites), affected_users_estimate=affected_users)
        updated = self.manager.update(incident.incident_id, actor=detected_by, changes={"decision_records": incident.decision_records + [self._decision_dict(classification)]})
        self.timeline_recorder.record(updated.incident_id, event_type="detection", description="incident detected and logged", performed_by=detected_by, automated=detection_method in {DetectionMethod.MONITORING, DetectionMethod.AUTOMATED_RULE})
        if updated.severity == IncidentSeverity.P1_CRITICAL:
            try:
                self.war_room_coordinator.initiate(updated, incident_commander=updated.assigned_to or detected_by, participants=[detected_by], current_diagnosis_summary="incident detected; diagnosis pending")
            except ValueError as error:
                self.assumptions.append(make_assumption(f"{updated.incident_id}:war_room", str(error), "P1 war room requires a human incident commander", True))
        self._audit("incident.detected", detected_by, updated, "success")
        self.decisions.append(make_decision("IncidentOrchestrator", f"{updated.incident_id}:detection", "detect_log_classify", "detection is logged before notification or diagnosis", ["detect_log_classify", "skip_logging"], {"detect_log_classify": "selected", "skip_logging": "rejected"}))
        return updated

    def acknowledge(self, incident_id: str, *, actor: str) -> Incident:
        """Acknowledge an incident and move it to investigating."""
        acknowledged = self.manager.transition(incident_id, actor=actor, status=IncidentStatus.ACKNOWLEDGED, description="incident acknowledged by assigned human")
        return self.manager.transition(incident_id, actor=actor, status=IncidentStatus.INVESTIGATING, description="investigation started")

    def notify(self, incident_id: str, *, actor: str, audience: str, channel: str = "email", language: str = "en", communication_type: str = "initial_notification") -> Communication:
        """Generate a communication artifact; external sending is not performed."""
        incident = self.manager.get(incident_id)
        communication = self.communication_manager.generate(incident, communication_type=communication_type, audience=audience, channel=channel, language=language)
        updated = self.manager.update(incident_id, actor=actor, changes={"communications": list(incident.communications) + [communication]})
        self.timeline_recorder.record(incident_id, event_type="notification_generated", description=f"{communication_type} communication artifact generated for {audience}", performed_by=actor)
        return communication

    def assess_impact(self, incident_id: str, *, actor: str, dependency_map: Mapping[str, Sequence[str]] | None = None, topology_links: Mapping[str, Sequence[str]] | None = None, business_impact: Mapping[str, Any] | None = None, compliance_context: Mapping[str, Any] | None = None) -> Incident:
        """Assess impact and persist the assessment."""
        incident = self.manager.get(incident_id)
        impact = self.impact_assessor.assess(affected_devices=incident.affected_devices, affected_services=incident.affected_services, affected_sites=incident.affected_sites, affected_users=incident.affected_users_estimate, dependency_map=dependency_map, topology_links=topology_links, business_impact=business_impact, compliance_context=compliance_context)
        return self.manager.update(incident_id, actor=actor, changes={"impact_assessment": impact})

    def diagnose(self, incident_id: str, *, actor: str, diagnostic_kwargs: Mapping[str, Any]) -> Incident:
        """Invoke the Troubleshooting Engine through an injected adapter."""
        incident = self.manager.get(incident_id)
        if incident.status != IncidentStatus.INVESTIGATING:
            raise ValueError("incident must be investigating before diagnosis")
        kwargs = dict(diagnostic_kwargs)
        if "symptom_input" not in kwargs and "symptom" not in kwargs:
            raise ValueError("diagnostic_kwargs must supply symptom_input or symptom")
        if self.troubleshooting_orchestrator is None:
            self.assumptions.append(make_assumption(f"{incident_id}:diagnosis", "not_connected", "Troubleshooting Engine adapter was not supplied", True))
            raise RuntimeError("troubleshooting orchestrator is not configured")
        result = self.troubleshooting_orchestrator.diagnose(**kwargs)
        diagnostic_id = str(getattr(result, "diagnostic_id", ""))
        rca = getattr(result, "root_cause_analysis", None)
        root_cause = str(getattr(rca, "root_cause", "")) if rca is not None else ""
        updated = self.manager.update(incident_id, actor=actor, changes={"diagnostic_session_id": diagnostic_id or None, "root_cause": root_cause})
        self.timeline_recorder.record(incident_id, event_type="diagnosis_completed", description="Troubleshooting Engine diagnosis completed with evidence-bounded result", performed_by=actor, evidence=list(getattr(result, "evidence_ids", [])))
        return updated

    def plan_containment(self, incident_id: str, *, actor: str, explicit_alternate_path: str | None = None, backup_reference: str | None = None) -> ContainmentPlan:
        """Create a containment plan and enter containment review state."""
        incident = self.manager.get(incident_id)
        if incident.status not in {IncidentStatus.INVESTIGATING, IncidentStatus.CONTAINED}:
            raise ValueError("incident must be investigating or contained before containment planning")
        plan = self.containment_planner.plan(incident_id=incident_id, category=incident.category, severity=incident.severity, affected_devices=incident.affected_devices, affected_services=incident.affected_services, related_change_ids=incident.related_changes, explicit_alternate_path=explicit_alternate_path, backup_reference=backup_reference)
        if incident.status == IncidentStatus.INVESTIGATING:
            self.manager.transition(incident_id, actor=actor, status=IncidentStatus.CONTAINMENT, description="containment plan prepared for human review")
        self.manager.update(incident_id, actor=actor, changes={"containment_plan": plan})
        self.timeline_recorder.record(incident_id, event_type="containment_plan", description="containment plan generated; no action executed", performed_by=actor)
        return plan

    def approve_containment(self, incident_id: str, *, actor: str, approval_reference: str) -> ContainmentPlan:
        """Record human approval without executing containment."""
        if not approval_reference or not actor:
            raise ValueError("actor and approval_reference are required")
        incident = self.manager.get(incident_id)
        self._require_governance_approval("containment", incident, actor, approval_reference)
        if incident.containment_plan is None:
            raise ValueError("containment plan is not present")
        plan = incident.containment_plan.model_copy(update={"execution_allowed": True, "approval_reference": approval_reference})
        self.manager.update(incident_id, actor=actor, changes={"containment_plan": plan})
        self.timeline_recorder.record(incident_id, event_type="containment_approved", description="human approval recorded; execution remains external to V1", performed_by=actor, evidence=[approval_reference])
        return plan

    def record_containment(self, incident_id: str, *, actor: str, execution_reference: str, outcome: str, evidence: Sequence[str] = ()) -> Incident:
        """Record a human-reported containment outcome."""
        incident = self.manager.get(incident_id)
        if incident.containment_plan is None or not incident.containment_plan.execution_allowed:
            raise ValueError("containment requires explicit human approval before an outcome can be recorded")
        status = IncidentStatus.CONTAINED if outcome.lower() in {"success", "contained", "completed"} else IncidentStatus.CONTAINMENT
        updated = self.manager.transition(incident_id, actor=actor, status=status, description=f"human-reported containment outcome: {outcome}", evidence=[execution_reference, *evidence]) if status == IncidentStatus.CONTAINED else incident
        self._audit("incident.containment_outcome", actor, updated, outcome)
        return updated

    def plan_eradication(self, incident_id: str, *, actor: str, root_cause_confidence: float, change_request_reference: str | None = None, vendor_case_reference: str | None = None, firmware_reference: str | None = None) -> EradicationPlan:
        """Create governed eradication plan."""
        incident = self.manager.get(incident_id)
        if incident.status not in {IncidentStatus.CONTAINED, IncidentStatus.INVESTIGATING}:
            raise ValueError("incident must be contained or investigating before eradication planning")
        plan = self.eradication_planner.plan(incident_id=incident_id, category=incident.category, root_cause=incident.root_cause, root_cause_confidence=root_cause_confidence, change_request_reference=change_request_reference, vendor_case_reference=vendor_case_reference, firmware_reference=firmware_reference)
        if incident.status == IncidentStatus.CONTAINED:
            self.manager.transition(incident_id, actor=actor, status=IncidentStatus.ERADICATING, description="eradication plan prepared for human approval")
        self.manager.update(incident_id, actor=actor, changes={"eradication_plan": plan})
        return plan

    def approve_eradication(self, incident_id: str, *, actor: str, approval_reference: str) -> EradicationPlan:
        """Record human approval for eradication plan without executing it."""
        incident = self.manager.get(incident_id)
        self._require_governance_approval("eradication", incident, actor, approval_reference)
        if incident.eradication_plan is None:
            raise ValueError("eradication plan is not present")
        plan = incident.eradication_plan.model_copy(update={"execution_allowed": True, "change_request_reference": incident.eradication_plan.change_request_reference or approval_reference})
        self.manager.update(incident_id, actor=actor, changes={"eradication_plan": plan})
        self.timeline_recorder.record(incident_id, event_type="eradication_approved", description="human approval recorded; execution remains outside V1 orchestrator", performed_by=actor, evidence=[approval_reference])
        return plan

    def plan_recovery(self, incident_id: str, *, actor: str, services: Sequence[Mapping[str, Any]], mode: str = "full_recovery") -> RecoveryPlan:
        """Create ordered service recovery plan."""
        incident = self.manager.get(incident_id)
        if incident.status not in {IncidentStatus.ERADICATING, IncidentStatus.CONTAINED}:
            raise ValueError("incident must be eradicating or contained before recovery planning")
        plan = self.recovery_planner.plan(incident_id=incident_id, services=services, mode=mode)
        if incident.status == IncidentStatus.ERADICATING:
            self.manager.transition(incident_id, actor=actor, status=IncidentStatus.RECOVERING, description="recovery plan prepared")
        self.manager.update(incident_id, actor=actor, changes={"recovery_plan": plan})
        return plan

    def record_recovery(self, incident_id: str, *, actor: str, execution_reference: str, verification_evidence: Sequence[str], outcome: str) -> Incident:
        """Record human-reported recovery and move to monitoring only after a positive outcome."""
        incident = self.manager.get(incident_id)
        if incident.recovery_plan is None:
            raise ValueError("recovery plan is not present")
        if outcome.lower() not in {"success", "recovered", "completed"}:
            return incident
        plan = incident.recovery_plan.model_copy(update={"execution_allowed": True})
        self.manager.update(incident_id, actor=actor, changes={"recovery_plan": plan})
        updated = self.manager.transition(incident_id, actor=actor, status=IncidentStatus.MONITORING, description="human-reported recovery completed; monitoring confirmation pending", evidence=[execution_reference, *verification_evidence])
        return updated

    def verify_and_resolve(self, incident_id: str, *, actor: str, verification: Mapping[str, bool], resolution: str) -> Incident:
        """Resolve only when connectivity, service, and monitoring checks are explicitly true."""
        incident = self.manager.get(incident_id)
        required = {"connectivity", "service", "monitoring"}
        missing = required - set(verification)
        if missing:
            raise ValueError(f"verification is missing: {sorted(missing)}")
        if not all(bool(verification[key]) for key in required):
            self.timeline_recorder.record(incident_id, event_type="verification_failed", description="recovery verification did not pass all required checks", performed_by=actor)
            return incident
        if incident.status != IncidentStatus.MONITORING:
            raise ValueError("incident must be monitoring before resolution")
        updated = self.manager.update(incident_id, actor=actor, changes={"resolution": resolution})
        return self.manager.transition(incident_id, actor=actor, status=IncidentStatus.RESOLVED, description="service recovery verified by explicit connectivity, service, and monitoring evidence")

    def close(self, incident_id: str, *, actor: str, review: IncidentReview | None = None, lessons: Sequence[Any] = ()) -> Incident:
        """Close an incident only after required post-incident review."""
        incident = self.manager.get(incident_id)
        if incident.status != IncidentStatus.RESOLVED:
            raise ValueError("only resolved incidents can be closed")
        if incident.severity in {IncidentSeverity.P1_CRITICAL, IncidentSeverity.P2_HIGH} and (review is None or review.required is False):
            raise ValueError("P1 and P2 incidents require a completed post-incident review before closure")
        if review is not None:
            self.timeline_recorder.record(incident_id, event_type="post_incident_review", description="post-incident review attached before closure", performed_by=actor)
        if lessons:
            self.manager.update(incident_id, actor=actor, changes={"lessons_learned": list(lessons)})
        return self.manager.transition(incident_id, actor=actor, status=IncidentStatus.CLOSED, description="incident closed after verification and required review")

    def evaluate_escalation(self, incident_id: str, *, elapsed: Any | None = None, scope_spreading: bool = False, diagnosis_exceeds_team: bool = False) -> EscalationDecision:
        """Evaluate escalation and persist level when higher."""
        incident = self.manager.get(incident_id)
        decision = self.escalation_engine.evaluate(incident, elapsed=elapsed, scope_spreading=scope_spreading, diagnosis_exceeds_team=diagnosis_exceeds_team)
        if decision.level > incident.escalation_level:
            self.manager.update(incident_id, actor="incident-governance", changes={"escalation_level": decision.level})
        return decision

    def activate_dr(self, incident_id: str, *, actor: str, approval_reference: str, activation_context: Mapping[str, Any]) -> Any:
        """Request a human-approved DR/BC activation through an optional adapter."""
        incident = self.manager.get(incident_id)
        if not approval_reference or not actor:
            raise ValueError("actor and approval_reference are required")
        if self.integrations.dr_bc is None:
            self.assumptions.append(make_assumption(f"{incident_id}:dr_bc", "not_connected", "DR/BC activation requires an explicitly configured adapter", True))
            raise RuntimeError("DR/BC adapter is not configured")
        response = self.integrations.dr_bc({"action": "activate_dr_review", "incident_id": incident_id, "actor": actor, "approval_reference": approval_reference, "context": dict(activation_context), "execute": False})
        self.timeline_recorder.record(incident_id, event_type="dr_bc_review", description="DR/BC activation request sent to configured adapter; network execution remains external", performed_by=actor, evidence=[approval_reference])
        return response

    def integration_status(self) -> dict[str, bool]:
        """Return optional cross-layer adapter configuration status."""
        return self.integrations.configured()

    def track_sla(self, incident_id: str, *, now: datetime | None = None) -> SLATracking:
        """Return current SLA tracking."""
        return self.sla_tracker.evaluate(self.manager.get(incident_id), now=now)

    def review(self, incident_id: str, **kwargs: Any) -> IncidentReview:
        """Generate a post-incident review artifact."""
        return self.post_incident_reviewer.create_review(self.manager.get(incident_id), **kwargs)

    def _require_governance_approval(self, action: str, incident: Incident, actor: str, approval_reference: str) -> None:
        """Require an optional governance adapter when one is configured."""
        if self.integrations.governance is None:
            self.assumptions.append(make_assumption(f"{incident.incident_id}:governance:{action}", "local_approval_reference", "no governance adapter is configured; explicit approval reference remains human-review evidence", True))
            return
        response = self.integrations.governance({"action": f"approve_{action}", "incident_id": incident.incident_id, "actor": actor, "approval_reference": approval_reference, "execute": False})
        approved = bool(response.get("approved")) if isinstance(response, Mapping) else bool(response)
        if not approved:
            raise PermissionError(f"governance adapter rejected {action} approval")

    def _decision_dict(self, item: Any) -> dict[str, Any]:
        """Serialize a classification or decision object safely."""
        if isinstance(item, SeverityClassification):
            return {"component": "SeverityClassifier", "decision_id": item.decision_id, "choice": item.severity.value, "rationale": item.rationale, "factors": item.factors, "assumptions": item.assumptions}
        if isinstance(item, DecisionRecord):
            return decision_dict(item)
        return {"component": "IncidentOrchestrator", "value": str(item)}

    def _audit(self, event_type: str, actor: str, incident: Incident, outcome: str) -> None:
        """Record secret-safe lifecycle metadata."""
        if self.audit_trail is not None:
            self.audit_trail.record(event_type, actor, {"incident_id": incident.incident_id, "status": incident.status.value, "severity": incident.severity.value, "category": incident.category.value, "execution_by_orchestrator": False}, outcome=outcome, correlation_id=incident.incident_id)
