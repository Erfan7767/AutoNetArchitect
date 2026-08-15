"""End-to-end read-only Troubleshooting Engine orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
import uuid
from typing import Any, Mapping, Sequence

from audit.audit_trail import AuditTrail
from designers.base_designer import Assumption, DecisionRecord

from .correlation_engine import CorrelationEngine
from .diagnostic_reporter import DiagnosticReporter
from .diagnostic_session import DiagnosticSession
from .evidence_collector import EvidenceCollector
from .escalation_advisor import EscalationAdvisor
from .hypothesis_engine import HypothesisEngine
from .known_issue_matcher import KnownIssueMatcher
from .models import AnalysisMode, DiagnosticResult, DiagnosticStatus, EvidenceRequest, ImpactAssessment, SymptomInput
from .models.diagnostic_result_models import DiagnosticTimelineEvent
from .packet_path_analyzer import PacketPathAnalyzer
from .rca_engine import RCAEngine
from .recent_change_correlator import RecentChangeCorrelator
from .remediation_advisor import RemediationAdvisor
from .show_command_interpreter import InterpreterEngine
from .symptom_classifier import SymptomClassifier
from .diagnostic_workflows import (
    ACLFirewallDiagnostic,
    AuthenticationDiagnostic,
    BGPDiagnostic,
    ConnectivityDiagnostic,
    DHCPDiagnostic,
    DNSDiagnostic,
    FHRPDiagnostic,
    IntermittentDiagnostic,
    L2Diagnostic,
    NATDiagnostic,
    OSPFDiagnostic,
    PerformanceDiagnostic,
    PhysicalLayerDiagnostic,
    QoSDiagnostic,
    RedundancyDiagnostic,
    RoutingDiagnostic,
    STPDiagnostic,
    VPNDiagnostic,
    WirelessDiagnostic,
)


class DiagnosticOrchestrator:
    """Coordinate evidence-bounded diagnosis without executing write commands."""

    WORKFLOW_TYPES = {item.diagnostic_id: item for item in (
        ConnectivityDiagnostic, PerformanceDiagnostic, IntermittentDiagnostic, AuthenticationDiagnostic, RoutingDiagnostic, L2Diagnostic, STPDiagnostic, FHRPDiagnostic, NATDiagnostic, ACLFirewallDiagnostic, WirelessDiagnostic, VPNDiagnostic, DNSDiagnostic, DHCPDiagnostic, QoSDiagnostic, RedundancyDiagnostic, BGPDiagnostic, OSPFDiagnostic, PhysicalLayerDiagnostic,
    )}

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Create a local orchestrator with optional audit integration."""
        self.audit_trail = audit_trail
        self.symptom_classifier = SymptomClassifier()
        self.change_correlator = RecentChangeCorrelator()
        self.known_issue_matcher = KnownIssueMatcher()
        self.hypothesis_engine = HypothesisEngine()
        self.evidence_collector = EvidenceCollector()
        self.rca_engine = RCAEngine()
        self.remediation_advisor = RemediationAdvisor()
        self.escalation_advisor = EscalationAdvisor()
        self.reporter = DiagnosticReporter()
        self.correlation_engine = CorrelationEngine()
        self.packet_path_analyzer = PacketPathAnalyzer()
        self.interpreter_engine = InterpreterEngine()
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def diagnose(self, symptom_input: SymptomInput | Mapping[str, Any], *, analysis_mode: AnalysisMode | str = AnalysisMode.OFFLINE, evidence_requests: Sequence[EvidenceRequest] = (), design_data: Mapping[str, Any] | None = None, config_data: Mapping[str, Any] | None = None, parsed_output: Sequence[Mapping[str, Any]] = (), monitoring_data: Sequence[Mapping[str, Any]] = (), log_data: Sequence[Mapping[str, Any]] = (), change_history: Sequence[Mapping[str, Any]] = (), digital_twin_data: Sequence[Mapping[str, Any]] = (), learning_memory: Sequence[Mapping[str, Any]] = (), known_issues: Sequence[Mapping[str, Any]] = (), vendor: str = "", platform: str = "", version: str = "", live_collector: Any | None = None) -> DiagnosticResult:
        """Execute the complete diagnosis lifecycle in a read-only path."""
        symptom = symptom_input if isinstance(symptom_input, SymptomInput) else SymptomInput.model_validate(symptom_input)
        mode = AnalysisMode(analysis_mode)
        diagnostic_id = f"diag:{uuid.uuid4()}"
        session = DiagnosticSession(diagnostic_id, symptom.reported_by)
        classification = self.symptom_classifier.classify(symptom)
        session.transition("classified", "symptom classification completed")
        related_changes = self.change_correlator.correlate(symptom.affected_scope, change_history, feature_area=str(symptom.additional_context.get("feature_area", "")))
        known_matches = self.known_issue_matcher.match(classification, known_issues, vendor=vendor, platform=platform, version=version)
        hypotheses = self.hypothesis_engine.generate(classification, recent_changes=[item.model_dump(mode="json") for item in related_changes], known_issues=[item.model_dump(mode="json") for item in known_matches])
        session.transition("evidence_collection", "evidence collection started")
        collection = self.evidence_collector.collect(mode, evidence_requests, design_data=design_data, config_data=config_data, parsed_output=parsed_output, monitoring_data=monitoring_data, log_data=log_data, change_history=change_history, digital_twin_data=digital_twin_data, learning_memory=learning_memory, live_collector=live_collector)
        workflow_class = self.WORKFLOW_TYPES.get(classification.suggested_diagnostic_workflows[0], ConnectivityDiagnostic)
        workflow = workflow_class()
        session.transition("workflow_execution", f"workflow {workflow.diagnostic_id} selected", [item.evidence_id for item in collection.items])
        workflow_output = workflow.execute(collection, hypotheses[:8])
        evaluations = workflow_output.hypothesis_evaluations or [self.hypothesis_engine.evaluate(item, collection) for item in hypotheses[:8]]
        session.transition("rca", "root cause analysis started", workflow_output.evidence_ids)
        rca = self.rca_engine.analyze(hypotheses, evaluations, collection, known_issue_matches=known_matches)
        remediation = self.remediation_advisor.advise(diagnostic_id, rca, change_management_reference=str(symptom.additional_context.get("change_management_reference", "")) or None)
        session.transition("remediation_advice", "remediation advice generated", workflow_output.evidence_ids)
        duration_hours = symptom.additional_context.get("duration_hours")
        escalation = self.escalation_advisor.advise(symptom, rca, duration_hours=float(duration_hours) if duration_hours is not None else None, critical_service=bool(symptom.additional_context.get("critical_service", False)), impact_exceeds_team=bool(symptom.additional_context.get("impact_exceeds_team", False)))
        session.transition("escalation", "escalation evaluation completed", workflow_output.evidence_ids)
        impact = self._impact(symptom, collection)
        timeline = [DiagnosticTimelineEvent(timestamp=event.timestamp, event_type=event.event_type, description=event.description, evidence_ids=event.evidence_ids) for event in session.events]
        packet_path = self._packet_path(symptom, design_data, collection)
        evidence_ids = list(dict.fromkeys(item.evidence_id for item in collection.items))
        limitations = list(dict.fromkeys(collection.missing_required + workflow_output.interpreted_evidence.limitations + rca.unresolved_uncertainties + ["live mode is read-only and does not execute configuration or diagnostic write commands"]))
        status = DiagnosticStatus.COMPLETED if collection.complete and rca.root_cause_confidence >= 0.3 else DiagnosticStatus.PARTIALLY_COMPLETED if collection.items else DiagnosticStatus.BLOCKED_MISSING_EVIDENCE
        decision = DecisionRecord("DiagnosticOrchestrator", f"orchestration:{diagnostic_id}", status.value, "complete all safe diagnostic phases while preserving evidence and uncertainty", [item.value for item in DiagnosticStatus], {item.value: "not selected by current evidence state" for item in DiagnosticStatus if item != status})
        self.decisions.append(decision)
        result = DiagnosticResult(diagnostic_id=diagnostic_id, status=status, analysis_mode=mode.value, symptom_input=symptom, symptom_classification=classification, timeline=timeline, evidence=collection.items, evidence_requests=evidence_requests, hypotheses=hypotheses, hypothesis_evaluations=evaluations, root_cause_analysis=rca, impact_assessment=impact, remediation_plan=remediation, escalation=escalation, related_changes=[item.model_dump(mode="json") for item in related_changes], known_issue_matches=[item.model_dump(mode="json") for item in known_matches], packet_path=packet_path.model_dump(mode="json") if packet_path else None, decision_records=self._decisions_as_dict(session, workflow), assumptions=self._assumptions_as_dict(session, workflow, collection), evidence_ids=evidence_ids, limitations=limitations)
        session.transition("completed", "diagnostic result assembled", evidence_ids)
        self._audit(result)
        return result

    def _packet_path(self, symptom: SymptomInput, design_data: Mapping[str, Any] | None, collection: Any) -> Any | None:
        """Run packet path analysis only when all packet inputs are explicitly supplied."""
        context = symptom.additional_context
        source = context.get("source_ip")
        destination = context.get("destination_ip")
        if not source or not destination:
            return None
        return self.packet_path_analyzer.analyze(str(source), str(destination), str(context.get("protocol", "unknown")), int(context["port"]) if context.get("port") is not None else None, design_data=design_data, evidence=collection)

    @staticmethod
    def _impact(symptom: SymptomInput, collection: Any) -> ImpactAssessment:
        """Build impact only from supplied context and collection completeness."""
        context = symptom.additional_context
        confidence = 0.75 if context else 0.35 if collection.items else 0.0
        return ImpactAssessment(affected_scope=symptom.affected_scope, service_impact=str(context.get("service_impact", "unknown")), user_impact=str(context.get("user_impact", "unknown")), availability_impact=str(context.get("availability_impact", "unknown")), security_impact=str(context.get("security_impact", "unknown")), confidence=confidence, assumptions=[] if context else ["impact fields were not supplied and are not inferred"])

    @staticmethod
    def _decisions_as_dict(session: DiagnosticSession, workflow: Any) -> list[dict[str, Any]]:
        """Serialize component decisions without losing rationale."""
        return [{"designer": decision.designer, "decision_id": decision.decision_id, "choice": decision.choice, "rationale": decision.rationale, "alternatives": decision.alternatives, "rejection_reasons": decision.rejection_reasons} for decision in list(session.decisions) + list(workflow.decisions)]

    @staticmethod
    def _assumptions_as_dict(session: DiagnosticSession, workflow: Any, collection: Any) -> list[dict[str, Any]]:
        """Serialize component assumptions."""
        assumptions = list(session.assumptions) + list(workflow.assumptions)
        result = [{"key": assumption.key, "value": assumption.value, "rationale": assumption.rationale, "requires_validation": assumption.requires_validation} for assumption in assumptions]
        result.extend({"key": item, "value": "recorded", "rationale": "component supplied this missing-evidence marker", "requires_validation": True} for item in collection.assumptions)
        return result

    def _audit(self, result: DiagnosticResult) -> None:
        """Record diagnostic metadata through the existing hash-chain audit trail."""
        if self.audit_trail is None:
            return
        self.audit_trail.record("troubleshooting.session", result.symptom_input.reported_by, {"diagnostic_id": result.diagnostic_id, "analysis_mode": result.analysis_mode, "status": result.status.value, "severity": result.symptom_input.severity.value, "scope_type": result.symptom_input.affected_scope.scope_type.value, "root_cause_confidence": result.root_cause_analysis.root_cause_confidence, "evidence_ids": result.evidence_ids, "write_commands_executed": False}, outcome=result.status.value)
