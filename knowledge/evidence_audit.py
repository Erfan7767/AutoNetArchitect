"""Evidence audit trail."""
from __future__ import annotations
from datetime import datetime, timezone
from dataclasses import dataclass
@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit event."""
    action: str
    evidence_hash: str
    timestamp: datetime
    actor: str
    detail: str
class EvidenceAudit:
    """Record evidence registration, resolution, and revocation actions."""
    def __init__(self) -> None: self.events: list[AuditEvent] = []
    def record(self, action: str, evidence_hash: str, actor: str, detail: str = "") -> AuditEvent:
        """Append an audit event."""
        event = AuditEvent(action, evidence_hash, datetime.now(timezone.utc), actor, detail); self.events.append(event); return event
    def for_evidence(self, evidence_hash: str) -> list[AuditEvent]:
        """Return the complete audit chain for one evidence record."""
        return [event for event in self.events if event.evidence_hash == evidence_hash]
