"""Knowledge governance test."""
from datetime import date, timedelta
from knowledge.freshness_policy import FreshnessPolicy
from knowledge.evidence_models import EvidenceRecord
def test_expiry():
    item = EvidenceRecord(source_id="s", source_type="human_verified", claim_type="x", claim_value=1, confidence=.5, acquisition_method="human", freshness_expiry=date.today()-timedelta(days=1)); assert not FreshnessPolicy().is_fresh(item)
