"""Audit integration for expert overrides."""
from __future__ import annotations

from typing import Any

from audit.audit_trail import AuditTrail
from designers.base_designer import BaseDesigner

from .override_models import OverrideApplication, OverrideRequest


class OverrideAudit(BaseDesigner):
    """Record secret-safe, append-only override events."""

    def __init__(self, *, audit_trail: AuditTrail | None = None) -> None:
        """Initialize optional audit integration."""
        super().__init__("OverrideAudit")
        self.audit_trail = audit_trail
        self.record_decision("override_audit_policy", "append_only_provenance", "override events are retained and never replace the original decision audit")

    def record(self, request: OverrideRequest, application: OverrideApplication) -> Any:
        """Record request and outcome metadata without raw secrets."""
        details = {"override_id": request.override_id, "target_id": request.target_id, "target_type": request.target_type.value, "override_type": request.override_type.value, "project_id": request.scope.project_id, "workflow": request.scope.workflow, "scope_statement": request.scope.scope_statement, "target_ids": list(request.scope.target_ids), "device_ids": list(request.scope.device_ids), "site_ids": list(request.scope.site_ids), "environment": request.scope.environment, "impact": request.impact, "reason": request.reason, "decided_at": request.decided_at.isoformat(), "actor_role": request.actor_role, "machine_decision_id": request.machine_decision_id, "origin": application.origin.value, "status": application.status, "revalidation_status": application.revalidation_status.value, "revalidation_trigger_ids": list(application.revalidation_trigger_ids), "affected_artifact_ids": list(application.affected_artifact_ids), "evidence_ids": list(application.evidence_ids), "provenance_chain": list(application.provenance_chain)}
        self.record_decision(f"audit:{request.override_id}", application.status, "override audit metadata was prepared with original decision provenance")
        if self.audit_trail is None:
            return details
        return self.audit_trail.record("expert_override.applied", request.actor_id, details, outcome=application.status)
