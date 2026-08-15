"""Evidence-backed best-practice registry."""
from .evidence_registry import EvidenceRegistry
class BestPracticeRegistry:
    """Expose best practices only through evidence records."""
    def __init__(self, registry: EvidenceRegistry) -> None: self.registry = registry
    def register(self, evidence: object) -> object:
        """Register an evidence-backed practice."""
        if getattr(evidence, "claim_type", "") != "best_practice": raise ValueError("claim_type must be best_practice")
        return self.registry.register(evidence)
