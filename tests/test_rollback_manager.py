from deployment import RollbackAssessment, RollbackDecision, RollbackManager, RollbackRequest


def _request(**overrides):
    values = {
        "request_id": "rb-1",
        "scope": ("edge-1",),
        "baseline_artifact_ids": ("baseline-1",),
        "current_artifact_ids": ("current-1",),
        "safety_policy_confirmations": {"management_access": True, "authentication": True, "audit_logging": True, "segmentation": True, "rollback_artifact_retained": True},
        "validation_evidence_ids": ("lab-rb-1",),
        "evidence_ids": ("rb-e1",),
    }
    values.update(overrides)
    return RollbackRequest(**values)


def test_rollback_manager_assesses_safe_scoped_rollback_and_keeps_execution_non_authorized():
    manager = RollbackManager()
    assessment = manager.assess(_request())
    assert assessment.decision == RollbackDecision.READY_FOR_REVIEW.value
    assert assessment.production_execution_allowed is False
    assert all(assessment.safety_policies_preserved.values())
    executed = manager.execute(_request())
    assert executed.decision == RollbackDecision.PREVIEW_ONLY.value
    assert executed.production_execution_allowed is False


def test_rollback_manager_blocks_policy_violation_and_remote_destructive_request():
    disabled = manager = RollbackManager().assess(_request(safety_policy_confirmations={"management_access": False}))
    assert disabled.decision == RollbackDecision.BLOCKED_POLICY.value
    remote = RollbackManager().assess(_request(remote_destructive=True))
    assert remote.decision == RollbackDecision.BLOCKED_REMOTE_DESTRUCTIVE.value
