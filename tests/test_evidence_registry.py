"""Knowledge governance test."""
from knowledge.evidence_registry import EvidenceRegistry
from knowledge.evidence_models import EvidenceRecord
def test_registry():
    registry = EvidenceRegistry(); item = registry.register(EvidenceRecord(source_id="s", source_type="validated_lab", claim_type="support", claim_value=True, confidence=.8, acquisition_method="lab")); assert registry.query("support")[0].evidence_hash == item.evidence_hash
