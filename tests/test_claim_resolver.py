"""Knowledge governance test."""
from knowledge.claim_resolver import ClaimResolver
from knowledge.evidence_registry import EvidenceRegistry
from knowledge.source_catalog import SourceCatalog
from knowledge.evidence_models import Claim
def test_unknown_without_evidence():
    assert ClaimResolver(EvidenceRegistry(), SourceCatalog()).resolve(Claim(claim_type="support")).status == "unknown"
