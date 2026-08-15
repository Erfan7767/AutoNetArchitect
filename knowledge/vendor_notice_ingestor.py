"""Vendor advisory ingestion into EvidenceRecord."""
from __future__ import annotations
from datetime import date
from .evidence_models import EvidenceRecord
class VendorNoticeIngestor:
    """Convert a vendor notice into traceable evidence."""
    def ingest(self, source_id: str, vendor: str, claim_type: str, claim_value: object, publication_date: date, product_family: str | None = None) -> EvidenceRecord:
        """Create a vendor field-advisory evidence record."""
        return EvidenceRecord(source_id=source_id, source_type="field_advisory", vendor=vendor, product_family=product_family, claim_type=claim_type, claim_value=claim_value, confidence=.9, acquisition_method="vendor_notice", publication_date=publication_date)
