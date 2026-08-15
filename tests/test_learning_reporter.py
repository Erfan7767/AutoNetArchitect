from learning_memory.learning_reporter import LearningReporter
from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancyType
from learning_memory.failure_memory import FailureMemory
from learning_memory.recurrence_detector import RecurrenceDetector

def test_learning_reporter_summarizes_memory_and_evidence_gaps():
    record = DiscrepancyRecord(discrepancy_id="d-l", discrepancy_type=DiscrepancyType.UNSUPPORTED_CLAIM_INCIDENT, scenario_id="s-l", decision_id="decision-l", evidence_state="not_available", actual_outcome=ActualOutcome(status="blocked", summary="claim lacked evidence", source="review"))
    failure = FailureMemory().record(record, failure_id="f-l")
    pattern = RecurrenceDetector().detect((record,), (failure,))
    report = LearningReporter().generate(project_id="p-1", discrepancies=(record,), failures=(failure,), recurring_patterns=pattern)
    assert report.discrepancy_count == 1 and report.evidence_gaps and "Discrepancy & Failure Memory Report" in LearningReporter().to_markdown(report)
