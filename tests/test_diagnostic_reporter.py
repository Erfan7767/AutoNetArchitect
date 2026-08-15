from troubleshooting import DiagnosticOrchestrator, DiagnosticReporter
from troubleshooting.models import AffectedScope, AffectedScopeType, Severity, SymptomInput


def test_diagnostic_reporter_exports_json_and_bilingual_markdown():
    symptom = SymptomInput(symptom_description="no ip address from dhcp", affected_scope=AffectedScope(scope_type=AffectedScopeType.VLAN, identifiers=["VLAN10"]), severity=Severity.MEDIUM, reported_by="tester")
    result = DiagnosticOrchestrator().diagnose(symptom)
    reporter = DiagnosticReporter()
    payload = reporter.to_dict(result)
    markdown = reporter.to_markdown(result)
    assert payload["diagnostic_id"] == result.diagnostic_id
    assert "Issue Summary" in markdown
    assert "ملخص المشكلة" in markdown
    assert "write_commands_executed" in payload["report_metadata"]
