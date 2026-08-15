from datetime import datetime, timezone
from learning_memory.postmortem_model import PostmortemRecord, PostmortemStatus, TimelineEvent

def test_postmortem_model_retains_timeline_and_prevention():
    record = PostmortemRecord(postmortem_id="pm-1", scenario_id="s-1", discrepancy_ids=("d-1",), failure_ids=("f-1",), timeline=(TimelineEvent(event_id="e-1", timestamp=datetime.now(timezone.utc), description="deployment failed", source="audit", evidence_ids=("audit-1",)),), actual_impact="branch unavailable", root_cause="field pathway mismatch", contributing_factors=("unknown construction constraint",), corrective_actions=("revise pathway model",), prevention_recommendations=("require survey evidence",), human_correction="engineer selected alternate route", evidence_status="verified", evidence_ids=("survey-1",), status=PostmortemStatus.REVIEW_REQUIRED)
    assert record.timeline[0].evidence_ids and record.prevention_recommendations and record.status == PostmortemStatus.REVIEW_REQUIRED
