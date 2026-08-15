"""Validation gate before knowledge publication."""
from __future__ import annotations
from .ingestion_pipeline import KnowledgeItem
class ValidationPipeline:
    """Require identity, source, content, and evidence metadata before publish."""
    def validate(self, item: KnowledgeItem) -> list[str]:
        """Return validation errors; an empty list permits publication."""
        errors = []
        if not item.item_id: errors.append("missing item_id")
        if not item.source_id: errors.append("missing source_id")
        if not item.content_hash: errors.append("missing content_hash")
        if item.claim_value is None: errors.append("missing claim value")
        if item.source_type not in IngestionPipelineSourceTypes.values(): errors.append("unsupported source type")
        item.validation_errors = errors; item.status = "validated" if not errors else "blocked"
        return errors
class IngestionPipelineSourceTypes:
    """Shared source type validator."""
    @classmethod
    def values(cls) -> set[str]:
        """Return permitted source types."""
        return {"vendor_docs", "release_notes", "advisory", "internal_lab", "human_validated_field"}
