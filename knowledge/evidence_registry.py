"""Central evidence registry."""
from __future__ import annotations
from .evidence_models import EvidenceRecord
from .freshness_policy import FreshnessPolicy
class EvidenceRegistry:
    """Store, retrieve, revoke, and query traceable evidence."""
    def __init__(self, freshness: FreshnessPolicy | None = None) -> None: self.records: dict[str, EvidenceRecord] = {}; self.freshness = freshness or FreshnessPolicy()
    def register(self, evidence: EvidenceRecord) -> EvidenceRecord:
        """Register evidence by immutable content hash."""
        self.records[evidence.evidence_hash] = evidence; return evidence
    def query(self, claim_type: str, include_expired: bool = False) -> list[EvidenceRecord]:
        """Return non-revoked fresh evidence for a claim type."""
        return [record for record in self.records.values() if record.claim_type == claim_type and (include_expired or self.freshness.is_fresh(record))]
    def revoke(self, evidence_hash: str, reason: str) -> EvidenceRecord:
        """Revoke a claim and preserve the reason."""
        record = self.records[evidence_hash].model_copy(update={"revoked": True, "revocation_reason": reason}); self.records[evidence_hash] = record; return record
