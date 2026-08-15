from change_management import ChangeClassifier, ChangeRequest, ChangeType


def test_change_classifier_suggests_standard_and_records_decision():
    request = ChangeRequest("CHG-1", "Add VLAN", "Detailed", "alice")
    result = ChangeClassifier().classify(request, standard_catalog_id="STD-VLAN-001", production_environment=True)
    assert result.suggested_type == ChangeType.STANDARD.value
    assert request.change_type == ChangeType.STANDARD.value
    assert result.decision_record is not None
    assert result.decision_record.decision_id.startswith("CHG-1:")


def test_change_classifier_suggests_emergency_and_accepts_override():
    request = ChangeRequest("CHG-2", "Restore outage", "Detailed", "alice")
    result = ChangeClassifier().classify(request, urgent_restoration=True, human_override={"priority": "critical"})
    assert result.suggested_type == ChangeType.EMERGENCY.value
    assert result.suggested_priority == "critical"
    assert result.human_override_applied is True
