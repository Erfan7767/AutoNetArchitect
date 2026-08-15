"""Normalize incoming knowledge into evidence-ready structures."""
from __future__ import annotations
import hashlib, json
from .ingestion_pipeline import KnowledgeItem
class NormalizationEngine:
    """Canonicalize claim values and compute deterministic content hashes."""
    def normalize(self, item: KnowledgeItem) -> KnowledgeItem:
        """Normalize whitespace and mapping key order without changing meaning."""
        value = item.claim_value
        if isinstance(value, str): value = " ".join(value.split())
        elif isinstance(value, dict): value = {str(k): value[k] for k in sorted(value)}
        digest = hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()
        return KnowledgeItem(item.item_id, item.source_type, item.claim_type, value, item.source_id, digest, item.status, item.publication_state, item.freshness_state, list(item.validation_errors), item.ingested_at, item.changed_from)
