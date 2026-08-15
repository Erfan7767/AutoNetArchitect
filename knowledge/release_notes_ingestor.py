"""Vendor release note ingestion."""
from __future__ import annotations
from datetime import date
from .evidence_models import EvidenceRecord
class ReleaseNotesIngestor:
    """Convert release notes to version-scoped evidence."""
    def ingest(self, source_id: str, vendor: str, platform: str, claim_type: str, claim_value: object, publication_date: date, min_version: str | None = None, max_version: str | None = None) -> EvidenceRecord:
        """Create an official release-note evidence record."""
        return EvidenceRecord(source_id=source_id, source_type="vendor_release_notes", vendor=vendor, platform=platform, claim_type=claim_type, claim_value=claim_value, confidence=.95, acquisition_method="release_notes", publication_date=publication_date, min_version=min_version, max_version_if_known=max_version)
