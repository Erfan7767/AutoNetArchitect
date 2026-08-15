from incident_response.severity_classifier import SeverityClassifier
from incident_response.incident_models import IncidentSeverity


def test_severity_classifier_applies_thresholds_and_sector_override():
    classifier = SeverityClassifier()
    result = classifier.classify(affected_users=1200, service_criticality="normal", business_impact="major", business_hours=True, workaround_available=False, duration_expected_minutes=60)
    assert result.severity == IncidentSeverity.P1_CRITICAL
    banking = classifier.classify(affected_users=1, service_criticality="core_banking", business_impact="normal", business_hours=False, workaround_available=True, duration_expected_minutes=10, sector="banking")
    assert banking.severity == IncidentSeverity.P1_CRITICAL


def test_severity_classifier_records_unknown_inputs():
    result = SeverityClassifier().classify(affected_users=None, service_criticality="normal", business_impact="unknown", business_hours=None, workaround_available=None, duration_expected_minutes=None)
    assert result.assumptions
