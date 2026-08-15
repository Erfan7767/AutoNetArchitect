from learning_memory.correction_patterns import CorrectionPatternDetector
from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyRecord, DiscrepancyType, HumanCorrection

def _record(identifier):
    return DiscrepancyRecord(discrepancy_id=identifier, discrepancy_type=DiscrepancyType.EQUIPMENT_MISMATCH, scenario_id="s-c", decision_id="d-c", evidence_state="partially_verified", actual_outcome=ActualOutcome(status="failed", summary="unsupported optic", source="deployment", evidence_ids=("ev-c",)), human_correction=HumanCorrection(correction_id=f"corr-{identifier}", actor_id="eng", actor_role="engineer", action="replace_equipment", rationale="capability evidence differs", evidence_ids=("cap-1",)))

def test_correction_detector_groups_repeated_human_action():
    patterns = CorrectionPatternDetector().detect((_record("d-c1"), _record("d-c2")))
    assert len(patterns) == 1 and patterns[0].occurrence_count == 2 and patterns[0].correction_ids
