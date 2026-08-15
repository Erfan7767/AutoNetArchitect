"""Publication state registry for active knowledge."""
from __future__ import annotations
from .ingestion_pipeline import KnowledgeItem
from .validation_pipeline import ValidationPipeline
class PublicationRegistry:
    """Publish only validated items and keep publication history."""
    def __init__(self, validator: ValidationPipeline | None = None) -> None: self.items: dict[str, KnowledgeItem] = {}; self.history: list[tuple[str, str]] = []; self.validator = validator or ValidationPipeline()
    def publish(self, item: KnowledgeItem) -> KnowledgeItem:
        """Validate and publish an item, otherwise block it."""
        errors = self.validator.validate(item)
        if errors: item.publication_state = "blocked"; self.history.append((item.item_id, "blocked")); return item
        item.publication_state = "published"; item.status = "published"; item.freshness_state = "fresh"; self.items[item.item_id] = item; self.history.append((item.item_id, "published")); return item
    def active(self, item_id: str) -> KnowledgeItem | None:
        """Return a published non-blocked item."""
        item = self.items.get(item_id); return item if item and item.publication_state == "published" and item.freshness_state == "fresh" else None
