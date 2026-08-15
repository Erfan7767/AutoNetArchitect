"""Policy for conflicts among evidence records."""
from __future__ import annotations
from dataclasses import dataclass
from .evidence_models import EvidenceRecord
from .source_catalog import SourceCatalog
@dataclass(frozen=True)
class ConflictOutcome:
    """Selected evidence and explicit conflict status."""
    status: str
    selected: EvidenceRecord | None
    competing: list[EvidenceRecord]
    rationale: str
class EvidenceConflictPolicy:
    """Prefer verified authoritative evidence but expose unresolved conflicts."""
    def resolve(self, records: list[EvidenceRecord], catalog: SourceCatalog) -> ConflictOutcome:
        """Resolve by authority, confidence, and publication date without hiding ties."""
        if not records: return ConflictOutcome("no_evidence", None, [], "no records")
        ranked = sorted(records, key=lambda r: (catalog.rank(r.source_id), r.confidence, r.publication_date or r.ingestion_date.date()), reverse=True); selected = ranked[0]; same_value = [r for r in ranked if r.claim_value == selected.claim_value]
        if len(same_value) != len(ranked): return ConflictOutcome("conflict_resolved_with_caveat", selected, ranked[1:], "highest authority and confidence selected; competing values retained")
        return ConflictOutcome("consistent", selected, [], "all evidence agrees")
