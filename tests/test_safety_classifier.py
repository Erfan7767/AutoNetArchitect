from deployment import SafetyClass, SafetyClassifier


def test_safety_classifier_distinguishes_read_only_disruptive_and_remote_destructive():
    classifier = SafetyClassifier()
    read_only = classifier.classify("op-1", "discover")
    assert read_only.safety_class == SafetyClass.READ_ONLY.value
    assert read_only.rollback_risk == "low"
    assert read_only.allowed is True
    disruptive = classifier.classify("op-2", "change_routing", rollback_artifact_available=True)
    assert disruptive.safety_class == SafetyClass.DISRUPTIVE.value
    assert disruptive.rollback_risk == "high"
    assert disruptive.allowed is True
    blocked = classifier.classify("op-3", "replace_config", remote=True, destructive=True, rollback_artifact_available=True)
    assert blocked.safety_class == SafetyClass.REMOTE_DESTRUCTIVE.value
    assert blocked.allowed is False


def test_safety_classifier_blocks_unapproved_production_request():
    assessment = SafetyClassifier().classify("op-4", "reload", rollback_artifact_available=True, production_requested=True, human_change_approval=False)
    assert assessment.allowed is False
    assert "human_change_approval" in assessment.required_approvals
