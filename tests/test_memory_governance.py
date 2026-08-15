from learning_memory.lesson_model import EvidenceStatus, LessonRecord, LessonStatus
from learning_memory.memory_governance import MemoryGovernance

def _lesson(status, evidence_status, evidence_ids):
    return LessonRecord(lesson_id=f"lesson-{status.value}-{evidence_status.value}", root_cause="root cause", corrective_action="corrective action", prevention_recommendation="prevention", status=status, evidence_status=evidence_status, evidence_ids=evidence_ids, confidence=0.8)

def test_memory_governance_blocks_unreviewed_unverified_lesson():
    decision = MemoryGovernance().assess_publication(_lesson(LessonStatus.DRAFT, EvidenceStatus.NOT_AVAILABLE, ()))
    assert not decision.allowed and decision.status == LessonStatus.REVIEW_REQUIRED

def test_memory_governance_publishes_validated_evidenced_lesson():
    governance = MemoryGovernance()
    lesson = _lesson(LessonStatus.VALIDATED, EvidenceStatus.VERIFIED, ("ev-1",))
    assert governance.publish(lesson).status == LessonStatus.PUBLISHED and governance.published()
