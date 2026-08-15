"""Evidence-only claim resolution."""
from __future__ import annotations
from typing import Any
from .evidence_models import Claim
from .evidence_registry import EvidenceRegistry
from .source_catalog import SourceCatalog
from .evidence_conflict_policy import EvidenceConflictPolicy
from .freshness_policy import FreshnessPolicy
class ClaimResolution:
    """Resolved, unverified, or conflicting claim with evidence chain."""
    def __init__(self, status: str, value: Any, evidence: list[object], rationale: str) -> None: self.status, self.value, self.evidence, self.rationale = status, value, evidence, rationale
class ClaimResolver:
    """Resolve claims only when a traceable evidence chain exists."""
    def __init__(self, registry: EvidenceRegistry, catalog: SourceCatalog) -> None: self.registry, self.catalog, self.policy = registry, catalog, EvidenceConflictPolicy()
    def resolve(self, claim: Claim) -> ClaimResolution:
        """Resolve a claim and never promote unsupported free text to fact."""
        records = self.registry.query(claim.claim_type); outcome = self.policy.resolve(records, self.catalog)
        if outcome.selected is None: return ClaimResolution("unknown", None, [], "no traceable evidence")
        status = "verified" if outcome.status == "consistent" else "verified_with_conflict_caveat"; return ClaimResolution(status, outcome.selected.claim_value, [outcome.selected, *outcome.competing], outcome.rationale)
