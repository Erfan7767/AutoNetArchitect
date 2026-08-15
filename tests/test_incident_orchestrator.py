from datetime import datetime, timezone
import tempfile
from audit.audit_trail import AuditTrail
from incident_response import IncidentOrchestrator
from incident_response.incident_models import DetectionMethod, IncidentCategory, IncidentSeverity
from troubleshooting import DiagnosticOrchestrator
from troubleshooting.models import AffectedScope, AffectedScopeType, Severity, SymptomInput

def test_incident_orchestrator_enforces_human_approval_and_full_lifecycle():
    orchestrator = IncidentOrchestrator()
    incident = orchestrator.detect(title="Config issue", description="Wrong policy", detected_by="alice", detection_method=DetectionMethod.ENGINEER, affected_users=20, service_criticality="standard", business_impact="moderate", category=IncidentCategory.CONFIGURATION_ERROR, affected_devices=["r1"], affected_services=["dns"], business_hours=True, workaround_available=False, duration_expected_minutes=30)
    orchestrator.acknowledge(incident.incident_id, actor="alice")
    plan = orchestrator.plan_containment(incident.incident_id, actor="alice")
    assert plan.execution_allowed is False
    approved = orchestrator.approve_containment(incident.incident_id, actor="alice", approval_reference="approval://contain-1")
    assert approved.execution_allowed is True
    orchestrator.record_containment(incident.incident_id, actor="alice", execution_reference="exec://contain-1", outcome="success")
    eradication = orchestrator.plan_eradication(incident.incident_id, actor="alice", root_cause_confidence=0.8, change_request_reference="change://1")
    assert eradication.execution_allowed is False
    orchestrator.approve_eradication(incident.incident_id, actor="alice", approval_reference="approval://erad-1")
    orchestrator.plan_recovery(incident.incident_id, actor="alice", services=[{"service_id":"dns", "tier":"core"}])
    orchestrator.record_recovery(incident.incident_id, actor="alice", execution_reference="exec://recovery-1", verification_evidence=["ev-1"], outcome="success")
    orchestrator.verify_and_resolve(incident.incident_id, actor="alice", verification={"connectivity":True, "service":True, "monitoring":True}, resolution="policy corrected")
    review = orchestrator.review(incident.incident_id)
    closed = orchestrator.close(incident.incident_id, actor="alice", review=review)
    assert closed.status.value == "closed"


def test_incident_orchestrator_integrates_troubleshooting_and_audit():
    audit_path = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    orchestrator = IncidentOrchestrator(audit_trail=AuditTrail(audit_path), troubleshooting_orchestrator=DiagnosticOrchestrator())
    incident = orchestrator.detect(title="Connectivity issue", description="Gateway unreachable", detected_by="alice", detection_method=DetectionMethod.MONITORING, affected_users=20, service_criticality="standard", business_impact="moderate", category=IncidentCategory.NETWORK_OUTAGE, affected_devices=["r1"], business_hours=True, workaround_available=False, duration_expected_minutes=30)
    orchestrator.acknowledge(incident.incident_id, actor="alice")
    symptom = SymptomInput(symptom_description="users cannot reach the gateway", affected_scope=AffectedScope(scope_type=AffectedScopeType.DEVICE, identifiers=["r1"]), severity=Severity.HIGH, reported_by="alice")
    diagnosed = orchestrator.diagnose(incident.incident_id, actor="alice", diagnostic_kwargs={"symptom_input": symptom})
    assert diagnosed.diagnostic_session_id
    assert len(orchestrator.audit_trail.query(event_type="incident.detected")) == 1


def test_incident_orchestrator_does_not_diagnose_without_adapter():
    orchestrator = IncidentOrchestrator()
    incident = orchestrator.detect(title="Issue", description="Issue", detected_by="alice", detection_method=DetectionMethod.ENGINEER, affected_users=1, service_criticality="normal", business_impact="minor", category=IncidentCategory.NETWORK_DEGRADATION, business_hours=False, workaround_available=True, duration_expected_minutes=10)
    orchestrator.acknowledge(incident.incident_id, actor="alice")
    try:
        orchestrator.diagnose(incident.incident_id, actor="alice", diagnostic_kwargs={})
    except ValueError as error:
        assert "symptom_input" in str(error)
    else:
        raise AssertionError("diagnosis without required input must be rejected")
