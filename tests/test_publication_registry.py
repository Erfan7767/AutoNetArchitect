"""Knowledge lifecycle test."""
from knowledge_lifecycle.ingestion_pipeline import IngestionPipeline
from knowledge_lifecycle.publication_registry import PublicationRegistry
def test_publish_gate():
    item = IngestionPipeline().ingest("i", "vendor_docs", "s", "support", True, "hash"); assert PublicationRegistry().publish(item).publication_state == "published"
