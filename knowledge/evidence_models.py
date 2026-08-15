"""Pydantic evidence, source, and claim contracts."""
from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Any
import hashlib, json
from pydantic import BaseModel, Field, ConfigDict
class EvidenceRecord(BaseModel):
    """Traceable evidence supporting one engineering or operational claim."""
    model_config = ConfigDict(extra="forbid")
    source_id: str
    source_type: str
    vendor: str | None = None
    product_family: str | None = None
    platform: str | None = None
    model: str | None = None
    min_version: str | None = None
    max_version_if_known: str | None = None
    license_scope: str | None = None
    claim_type: str
    claim_value: Any
    confidence: float
    acquisition_method: str
    publication_date: date | None = None
    ingestion_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    freshness_expiry: date | None = None
    region_scope: str | None = None
    support_scope: str | None = None
    evidence_hash: str = ""
    revoked: bool = False
    revocation_reason: str | None = None
    def model_post_init(self, __context: Any) -> None:
        """Compute a stable content hash when one is not supplied."""
        if not self.evidence_hash:
            payload = self.model_dump(mode="json", exclude={"evidence_hash", "ingestion_date"}); object.__setattr__(self, "evidence_hash", hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest())
        if not 0 <= self.confidence <= 1: raise ValueError("confidence must be between zero and one")
class SourceRecord(BaseModel):
    """Cataloged source with authority and traceability metadata."""
    source_id: str
    source_type: str
    name: str
    authority_rank: int
    uri: str | None = None
    publisher: str | None = None
    verified: bool = False
class Claim(BaseModel):
    """A requested claim resolved only through evidence."""
    claim_type: str
    subject: dict[str, str] = Field(default_factory=dict)
    requested_value: Any = None
