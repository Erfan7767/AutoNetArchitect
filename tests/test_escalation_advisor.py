from troubleshooting.escalation_advisor import EscalationAdvisor
from troubleshooting.models import AffectedScope, AffectedScopeType, Severity, SymptomInput, RootCauseAnalysis, RootCauseClassification


def _symptom():
    return SymptomInput(symptom_description="hardware failure", affected_scope=AffectedScope(scope_type=AffectedScopeType.DEVICE, identifiers=["r1"]), severity=Severity.CRITICAL, reported_by="tester")


def test_escalation_advisor_escalates_hardware_and_low_confidence():
    rca = RootCauseAnalysis(root_cause="unknown", root_cause_confidence=0.1, root_cause_classification=RootCauseClassification.HARDWARE_FAILURE, confidence_level="inconclusive")
    recommendation = EscalationAdvisor().advise(_symptom(), rca, critical_service=True)
    assert recommendation.required is True
    assert recommendation.targets


def test_escalation_advisor_does_not_escalate_when_no_criteria_supplied():
    symptom = SymptomInput(symptom_description="minor issue", affected_scope=AffectedScope(scope_type=AffectedScopeType.USER, identifiers=["u1"]), severity=Severity.LOW, reported_by="tester")
    rca = RootCauseAnalysis(root_cause="known configuration", root_cause_confidence=0.7, root_cause_classification=RootCauseClassification.CONFIGURATION_ERROR, confidence_level="medium")
    recommendation = EscalationAdvisor().advise(symptom, rca)
    assert recommendation.required is False
