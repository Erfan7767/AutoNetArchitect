"""Knowledge lifecycle test."""
from datetime import date, timedelta
from knowledge_lifecycle.ingestion_pipeline import KnowledgeItem
from knowledge_lifecycle.stale_claim_detector import StaleClaimDetector
def test_production_block():
    item = KnowledgeItem("i", "vendor_docs", "x", True, "s", "h", publication_state="published", freshness_state="stale"); assert not StaleClaimDetector().production_allowed(item)
