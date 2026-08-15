"""Lifecycle ingestion for authoritative knowledge sources."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
@dataclass
class KnowledgeItem:
    """Normalized lifecycle item with explicit status."""
    item_id: str
    source_type: str
    claim_type: str
    claim_value: Any
    source_id: str
    content_hash: str
    status: str = "ingested"
    publication_state: str = "unpublished"
    freshness_state: str = "unknown"
    validation_errors: list[str] = field(default_factory=list)
    ingested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changed_from: str | None = None
class IngestionPipeline:
    """Accept supported source classes and create lifecycle items."""
    SUPPORTED = {"vendor_docs", "release_notes", "advisory", "internal_lab", "human_validated_field"}
    def ingest(self, item_id: str, source_type: str, source_id: str, claim_type: str, claim_value: Any, content_hash: str) -> KnowledgeItem:
        """Create an ingested item without publishing it."""
        if source_type not in self.SUPPORTED: raise ValueError("unsupported ingestion source")
        if not item_id or not source_id or not content_hash: raise ValueError("identity and content hash are required")
        return KnowledgeItem(item_id, source_type, claim_type, claim_value, source_id, content_hash)
