from audit.audit_trail import AuditTrail
from troubleshooting import DiagnosticOrchestrator
from troubleshooting.models import AffectedScope, AffectedScopeType, AnalysisMode, Severity, SymptomInput, EvidenceRequest


def _symptom():
    return SymptomInput(symptom_description="users cannot reach the gateway after vlan change", affected_scope=AffectedScope(scope_type=AffectedScopeType.VLAN, identifiers=["VLAN10"], site_id="SITE-1"), severity=Severity.HIGH, reported_by="tester")


def test_diagnostic_orchestrator_completes_offline_or_partial_result_without_writes():
    result = DiagnosticOrchestrator().diagnose(_symptom(), design_data={"path_hops":[{"device_id":"edge-1", "decision":"drop", "acl_action":"deny"}]}, parsed_output=[{"target_device":"edge-1", "output":"interface down"}])
    assert result.analysis_mode == "offline"
    assert result.remediation_plan.execution_allowed is False
    assert result.packet_path is None
    assert result.decision_records
    assert all(step.read_only_preview for step in result.remediation_plan.steps)


def test_diagnostic_orchestrator_supports_live_read_only_and_blocks_without_collector():
    request = EvidenceRequest(evidence_type="interface_state", target_device="edge-1", command_or_query="show interfaces")
    blocked = DiagnosticOrchestrator().diagnose(_symptom(), analysis_mode=AnalysisMode.LIVE_READ_ONLY, evidence_requests=[request])
    assert blocked.status.value in {"blocked_missing_evidence", "partially_completed"}
    live = DiagnosticOrchestrator().diagnose(_symptom(), analysis_mode=AnalysisMode.LIVE_READ_ONLY, evidence_requests=[request], live_collector=lambda payload: {"operation":"collect_evidence", "read_only":True, "parsed_data":{"state":"up"}, "confidence":0.8})
    assert live.analysis_mode == "live_read_only"
    assert live.evidence


def test_diagnostic_orchestrator_records_audit_session():
    import tempfile
    path = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False).name
    audit = AuditTrail(path)
    result = DiagnosticOrchestrator(audit_trail=audit).diagnose(_symptom())
    assert result.diagnostic_id
    assert len(audit.query(event_type="troubleshooting.session")) == 1
