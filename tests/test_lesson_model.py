from learning_memory.lesson_model import EvidenceStatus, LessonRecord, LessonStatus

def test_lesson_model_captures_required_learning_fields():
    lesson = LessonRecord(lesson_id="lesson-1", scenario_ids=("s-1",), discrepancy_ids=("d-1",), failure_ids=("f-1",), decision_ids=("decision-1",), root_cause="unknown pathway constraint", contributing_factors=("incomplete survey",), evidence_status=EvidenceStatus.VERIFIED, evidence_ids=("survey-1",), corrective_action="update pathway model", prevention_recommendation="require field survey before final design", human_correction_summary="engineer replaced logical assumption", recurrence_count=1, confidence=0.9, status=LessonStatus.VALIDATED)
    assert lesson.root_cause and lesson.corrective_action and lesson.prevention_recommendation and lesson.evidence_status == EvidenceStatus.VERIFIED
