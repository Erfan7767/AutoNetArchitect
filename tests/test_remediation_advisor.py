from troubleshooting.models import RootCauseAnalysis, RootCauseClassification
from troubleshooting.remediation_advisor import RemediationAdvisor


def test_remediation_advisor_is_non_executing_for_low_confidence():
    rca = RootCauseAnalysis(root_cause="unknown", root_cause_confidence=0.1, root_cause_classification=RootCauseClassification.UNKNOWN, confidence_level="inconclusive")
    plan = RemediationAdvisor().advise("diag-1", rca)
    assert plan.execution_allowed is False
    assert plan.plan_type == "investigation"
    assert plan.steps


def test_remediation_advisor_requires_change_governance_for_supported_cause():
    rca = RootCauseAnalysis(root_cause="routing policy mismatch", root_cause_confidence=0.85, root_cause_classification=RootCauseClassification.CONFIGURATION_ERROR, confidence_level="high")
    plan = RemediationAdvisor().advise("diag-2", rca)
    assert plan.execution_allowed is False
    assert plan.steps[0].requires_change_request is True
