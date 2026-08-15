from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancySeverity, DiscrepancyType
from learning_memory.failure_memory import FailureMemory

def _record():
    return DiscrepancyRecord(discrepancy_id="d-f", discrepancy_type=DiscrepancyType.CONFIG_MISMATCH, severity=DiscrepancySeverity.MEDIUM, scenario_id="scenario-f", decision_id="decision-f", evidence_state="verified", actual_outcome=ActualOutcome(status="failed", summary="config drift", source="operations", evidence_ids=("op-1",)))

def test_failure_memory_retains_and_increments_recurring_failure():
    memory = FailureMemory()
    record = _record()
    first = memory.record(record, failure_id="failure-f")
    second = memory.record(record, failure_id="failure-f")
    assert first.retained_for_learning and second.occurrence_count == 2 and memory.recurring()

def test_failure_memory_links_lesson_and_postmortem():
    memory = FailureMemory()
    memory.record(_record(), failure_id="failure-link")
    assert memory.link_lesson("failure-link", "lesson-1").lesson_id == "lesson-1"
    assert memory.link_postmortem("failure-link", "pm-1").postmortem_id == "pm-1"
