"""Evidence freshness and revocation policy."""
from __future__ import annotations
from datetime import date, timedelta
from .evidence_models import EvidenceRecord
class FreshnessPolicy:
    """Determine validity and expiry of evidence."""
    DEFAULT_DAYS = {"vendor_official_docs": 730, "vendor_release_notes": 365, "field_advisory": 180, "standards_body": 1095, "validated_lab": 180, "human_verified": 90}
    def expiry_for(self, source_type: str, publication_date: date | None) -> date | None:
        """Calculate a conservative expiry date."""
        if publication_date is None: return None
        return publication_date + timedelta(days=self.DEFAULT_DAYS.get(source_type, 90))
    def is_fresh(self, evidence: EvidenceRecord, today: date | None = None) -> bool:
        """Return whether evidence is current and not revoked."""
        return not evidence.revoked and (evidence.freshness_expiry is None or evidence.freshness_expiry >= (today or date.today()))
    def revoke_if_expired(self, evidence: EvidenceRecord, today: date | None = None) -> EvidenceRecord:
        """Return a revoked copy when freshness has expired."""
        if not self.is_fresh(evidence, today): return evidence.model_copy(update={"revoked": True, "revocation_reason": "freshness_expired"})
        return evidence
