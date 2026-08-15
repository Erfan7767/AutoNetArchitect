"""Evaluate deployment operation, verification, and rollback evidence."""

from __future__ import annotations

from typing import Any

from .deployment_models import DeploymentOperation, DeploymentResult, DeploymentState


class DeploymentResultHandler:
    """Combine evidence into a conservative deployment result."""

    def handle(self, operation: DeploymentOperation, *, verification: Any = None, rollback: Any = None) -> DeploymentResult:
        """Return a result whose gate never exceeds its evidence."""
        evidence = set(operation.evidence_ids)
        reasons = list(operation.reasons)
        required_inputs: list[str] = []
        state = operation.state
        gate = "block_or_review"
        if operation.state == DeploymentState.DRY_RUN.value:
            state = DeploymentState.DRY_RUN.value
            gate = "review_only"
            reasons.append("dry-run result is not production evidence")
        elif operation.state not in {DeploymentState.EXECUTED.value, DeploymentState.VERIFIED.value}:
            gate = "blocked"
            if operation.state == DeploymentState.BLOCKED_BACKUP.value:
                required_inputs.append("backup_reference")
            if operation.state == DeploymentState.BLOCKED_HUMAN_DATA.value:
                required_inputs.extend(operation.reasons)
        elif verification is None:
            state = DeploymentState.VERIFICATION_PENDING.value
            required_inputs.append("post_deploy_verification_report")
            reasons.append("execution completed without post-deploy verification evidence")
        else:
            proof_status = str(getattr(verification, "proof_status", ""))
            production_suitable = bool(getattr(verification, "production_suitable", False))
            verification_evidence = getattr(verification, "evidence_basis", getattr(verification, "evidence_ids", ()))
            evidence.update(str(item) for item in verification_evidence)
            if proof_status == "verified" and production_suitable:
                state = DeploymentState.VERIFIED.value
                gate = "allow"
            elif proof_status == "failed":
                state = DeploymentState.FAILED.value
                gate = "block_or_review"
                reasons.append("post-deploy verification failed")
            else:
                state = DeploymentState.VERIFICATION_PENDING.value
                gate = "block_or_review"
                reasons.append("post-deploy evidence is incomplete or not fully verified")
                required_inputs.append("complete_post_deploy_verification")
        if rollback is not None:
            evidence.update(str(item) for item in getattr(rollback, "evidence_ids", ()))
        if state == DeploymentState.FAILED.value and rollback is not None:
            decision = str(getattr(rollback, "decision", ""))
            if decision in {"ready_for_review", "preview_only"}:
                state = DeploymentState.ROLLBACK_REVIEW.value
                reasons.append("rollback assessment is available for human review")
        return DeploymentResult(operation.deployment_id, state, gate, operation, verification, rollback, tuple(dict.fromkeys(required_inputs)), tuple(dict.fromkeys(reasons)), tuple(sorted(evidence)))
