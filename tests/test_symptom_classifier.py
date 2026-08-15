from troubleshooting.models import AffectedScope, AffectedScopeType, Severity, SymptomInput
from troubleshooting.symptom_classifier import SymptomClassifier


def test_symptom_classifier_detects_connectivity_and_subtype():
    symptom = SymptomInput(symptom_description="users have intermittent connectivity loss", affected_scope=AffectedScope(scope_type=AffectedScopeType.SERVICE, identifiers=["svc-1"]), severity=Severity.HIGH, reported_by="tester")
    result = SymptomClassifier().classify(symptom)
    assert result.primary_class.value == "connectivity_loss"
    assert result.confidence > 0.0
    assert result.suggested_diagnostic_workflows


def test_symptom_classifier_marks_unknown_input_with_assumption():
    result = SymptomClassifier().classify("an unfamiliar symptom")
    assert result.primary_class.value == "unknown"
    assert result.confidence < 0.5
    assert result.assumptions
