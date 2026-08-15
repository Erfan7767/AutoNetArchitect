from learning_memory.discrepancy_registry import ActualOutcome, DiscrepancyType
from learning_memory.feedback_ingestor import FeedbackIngestor, FeedbackRecord, FeedbackSource

def test_feedback_ingestor_supports_all_required_sources():
    ingestor = FeedbackIngestor()
    for index, source in enumerate(FeedbackSource):
        result = ingestor.ingest(FeedbackRecord(feedback_id=f"fb-{index}", source=source, scenario_id=f"scenario-{index}", decision_id=f"decision-{index}", discrepancy_type=DiscrepancyType.DEPLOYMENT_MISMATCH, evidence_state="verified", evidence_ids=(f"ev-{index}",), actual_outcome=ActualOutcome(status="failed", summary="observed mismatch", source=source.value, evidence_ids=(f"obs-{index}",))))
        assert result.source == source and result.discrepancy_id.startswith("discrepancy:") and result.failure_id.startswith("failure:")

def test_feedback_ingestor_links_human_correction():
    ingestor = FeedbackIngestor()
    result = ingestor.ingest(FeedbackRecord(feedback_id="fb-correction", source=FeedbackSource.HUMAN_REVIEW, scenario_id="s", decision_id="d", discrepancy_type=DiscrepancyType.DESIGN_MISMATCH, evidence_state="partially_verified", actual_outcome=ActualOutcome(status="corrected", summary="review changed design", source="review")))
    assert ingestor.discrepancy_registry.get(result.discrepancy_id).human_correction is None
