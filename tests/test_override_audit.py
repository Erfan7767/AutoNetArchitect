import tempfile
from audit.audit_trail import AuditTrail
from expert_override.override_audit import OverrideAudit
from expert_override.override_models import OverrideApplication, OverrideRequest, OverrideScope, OverrideTargetType, OverrideType, RevalidationStatus, DecisionOrigin
from datetime import datetime, timezone

def test_override_audit_records_secret_safe_metadata():
    with tempfile.NamedTemporaryFile(suffix=".jsonl") as handle:
        audit = AuditTrail(handle.name)
        request = OverrideRequest(override_id="ov-a", target_id="design-1", target_type=OverrideTargetType.DESIGN_DECISION, override_type=OverrideType.FORCE_ACCEPT, scope=OverrideScope(project_id="p-1", workflow="design", target_ids=("design-1",), scope_statement="bounded"), actor_id="eng", actor_role="engineer", reason="reason", impact="impact", machine_decision_id="machine-1")
        application = OverrideApplication(override_id="ov-a", target_id="design-1", target_type=request.target_type, override_type=request.override_type, status="applied", origin=DecisionOrigin.HUMAN_OVERRIDDEN, machine_decision_id="machine-1", original_value=False, resulting_value=True, provenance_chain=("machine-1", "ov-a"), actor_id="eng", actor_role="engineer", reason=request.reason, scope=request.scope, impact=request.impact, decided_at=datetime.now(timezone.utc), revalidation_status=RevalidationStatus.REQUIRED)
        OverrideAudit(audit_trail=audit).record(request, application)
        assert len(audit.query(event_type="expert_override.applied")) == 1
