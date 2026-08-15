from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancyType
from learning_memory.failure_memory import FailureMemory
from learning_memory.recurrence_detector import RecurrenceDetector

def _record(identifier):
    return DiscrepancyRecord(discrepancy_id=identifier, discrepancy_type=DiscrepancyType.FALSE_CONFIDENCE_INCIDENT, scenario_id="scenario-r", decision_id="decision-r", evidence_state="not_available", actual_outcome=ActualOutcome(status="failed", summary="confidence exceeded evidence", source="review", evidence_ids=("review-1",)))

def test_recurrence_detector_groups_repeated_fingerprint():
    first, second = _record("d-r1"), _record("d-r2")
    memory = FailureMemory()
    failures = (memory.record(first, failure_id="f-r1"), memory.record(second, failure_id="f-r2"))
    patterns = RecurrenceDetector().detect((first, second), failures)
    assert len(patterns) == 1 and patterns[0].threshold_reached and patterns[0].occurrence_count == 2

def test_recurrence_detector_fingerprint_is_explicit():
    assert "false_confidence_incident" in RecurrenceDetector.fingerprint(_record("d-r3"))
