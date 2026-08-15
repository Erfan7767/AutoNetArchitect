"""Source catalog and authority classification."""
from __future__ import annotations
from .evidence_models import SourceRecord
class SourceCatalog:
    """Catalog authoritative source classes and ranking."""
    DEFAULT_RANKS = {"vendor_official_docs": 100, "vendor_release_notes": 95, "field_advisory": 90, "standards_body": 85, "validated_lab": 80, "human_verified": 70}
    def __init__(self, sources: list[SourceRecord] | None = None) -> None: self.sources = {source.source_id: source for source in sources or []}
    def add(self, source: SourceRecord) -> None:
        """Add a verified source record."""
        if source.source_type not in self.DEFAULT_RANKS: raise ValueError("unsupported source type")
        self.sources[source.source_id] = source
    def get(self, source_id: str) -> SourceRecord:
        """Return a source or raise KeyError."""
        return self.sources[source_id]
    def rank(self, source_id: str) -> int:
        """Return effective authority rank."""
        source = self.get(source_id); return source.authority_rank if source.verified else min(source.authority_rank, 50)
