"""Evidence-backed standards registry."""
from .evidence_registry import EvidenceRegistry
class StandardsRegistry:
    """Expose standards claims only through evidence records."""
    def __init__(self, registry: EvidenceRegistry) -> None: self.registry = registry
    def register(self, evidence: object) -> object:
        """Register a standards evidence record."""
        if getattr(evidence, "source_type", "") != "standards_body": raise ValueError("source must be a standards body")
        return self.registry.register(evidence)
