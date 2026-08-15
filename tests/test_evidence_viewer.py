from datetime import date
from knowledge.evidence_models import EvidenceRecord
from review_console.evidence_viewer import EvidenceViewer

def test_evidence_viewer_shows_source_confidence_freshness_and_scope():
    evidence = EvidenceRecord(source_id="src-1", source_type="vendor_official", claim_type="capability", claim_value=True, confidence=0.9, acquisition_method="document", freshness_expiry=date(2099, 1, 1), support_scope="platform-x", region_scope="global")
    view = EvidenceViewer().build((evidence,), ("src-2",))
    assert view[0].evidence_id == "src-1" and view[0].confidence == 0.9 and view[1].status == "referenced_not_loaded"
