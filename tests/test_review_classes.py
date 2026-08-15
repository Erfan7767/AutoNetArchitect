from governance.review_classes import ReviewClass, ReviewClassRegistry, ReviewOutcome, ReviewRecord

def test_review_class_registry_exposes_required_roles():
    registry = ReviewClassRegistry()
    assert registry.role_for(ReviewClass.SECURITY) == "security_reviewer"
    assert registry.definition(ReviewClass.EMERGENCY).blocks_execution is True

def test_review_record_requires_rationale_when_decided():
    registry = ReviewClassRegistry()
    try:
        registry.record_review(ReviewRecord(review_id="rev-1", workflow="design", decision_class="security_decision", risk_class="high", review_class=ReviewClass.SECURITY, reviewer_id="sec-1", reviewer_role="security_reviewer", outcome=ReviewOutcome.ACCEPTED))
    except ValueError:
        return
    raise AssertionError("decided review without rationale was accepted")
