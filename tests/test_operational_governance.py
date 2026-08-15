from datetime import datetime, timezone
import tempfile

from audit.audit_trail import AuditTrail
from operations import DriftItem, DriftReport, DriftSeverity, OperationalGovernance


def _report(severity=DriftSeverity.HIGH.value):
    item = DriftItem("edge-1", "routing.state", "up", "down", severity, "drifted", evidence_ids=("ev-drift",))
    return DriftReport("DRIFT-1", "sot:operational:1", 1, datetime.now(timezone.utc).isoformat(), True, (item,), severity, "block_or_review", False, ("high-risk production drift requires explicit approval before any remediation",), ("ev-drift",))


def test_operational_governance_blocks_high_risk_remediation_without_approval():
    result = OperationalGovernance().remediate("DEC-1", _report(), production_requested=True, driver=lambda payload: {"status": "success"})
    assert result.executed is False
    assert result.state == "blocked"
    assert "approval_reference" in result.decision.required_human_inputs


def test_operational_governance_preview_never_invokes_driver():
    calls = []
    result = OperationalGovernance().preview("DEC-2", _report())
    assert result.executed is False
    assert result.state == "preview_only"
    assert calls == []


def test_operational_governance_executes_only_with_approval_and_sanitizes_output():
    audit_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    audit_file.close()
    audit = AuditTrail(audit_file.name)
    seen = []
    governance = OperationalGovernance(audit_trail=audit)
    result = governance.remediate("DEC-3", _report(), approval_reference="approval://CHG-1", production_requested=True, driver=lambda payload: seen.append(payload) or {"status": "success", "output": "password=raw-secret", "evidence_ids": ["ev-remediate"]})
    assert result.executed is True
    assert result.state == "executed"
    assert "raw-secret" not in result.output
    assert seen[0]["approval_reference"] == "approval://CHG-1"
    assert len(audit.query(event_type="operations.remediation")) == 1
