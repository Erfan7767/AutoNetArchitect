"""Registry of field advisories and revocations."""
from __future__ import annotations
from .evidence_registry import EvidenceRegistry
class FieldAdvisoryRegistry:
    """Register advisories and revoke contradicted evidence."""
    def __init__(self, registry: EvidenceRegistry) -> None: self.registry = registry; self.advisories = []
    def record(self, advisory: object) -> None:
        """Record an advisory evidence object."""
        self.advisories.append(advisory)
    def revoke_claim(self, claim_type: str, reason: str) -> int:
        """Revoke all active records of a contradicted claim type."""
        count = 0
        for evidence_hash, record in list(self.registry.records.items()):
            if record.claim_type == claim_type and not record.revoked: self.registry.revoke(evidence_hash, reason); count += 1
        return count
