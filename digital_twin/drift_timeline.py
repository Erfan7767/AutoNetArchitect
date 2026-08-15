"""Temporal drift ledger between intended and observed Digital Twin states."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .twin_model import TwinState


@dataclass(frozen=True)
class DriftEvent:
    """One time-indexed drift observation."""

    event_id: str
    timestamp: str
    entity_id: str
    field: str
    expected: Any
    observed: Any
    status: str
    source: str
    evidence_ids: tuple[str, ...] = ()
    certainty: str = "observed"

    def to_dict(self) -> dict[str, Any]:
        """Serialize drift event."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


class DriftTimeline:
    """Record and query drift over time without overwriting prior findings."""

    def __init__(self) -> None:
        """Create an empty drift timeline."""
        self._events: list[DriftEvent] = []

    def compare(self, expected: TwinState, observed: TwinState, timestamp: str | None = None) -> tuple[DriftEvent, ...]:
        """Compare state values field by field and retain only explicit differences."""
        time_value = timestamp or observed.provenance.observed_at or observed.provenance.ingested_at or ""
        differences: list[DriftEvent] = []
        fields = sorted(set(expected.values) | set(observed.values))
        for field_name in fields:
            expected_value = expected.values.get(field_name)
            observed_value = observed.values.get(field_name)
            if expected_value == observed_value:
                continue
            event_id = f"drift:{observed.entity_id}:{field_name}:{len(self._events) + len(differences) + 1}"
            event = DriftEvent(event_id, time_value, observed.entity_id, field_name, expected_value, observed_value, "drift", observed.provenance.source, tuple(dict.fromkeys(expected.provenance.evidence_ids + observed.provenance.evidence_ids)), observed.provenance.certainty)
            differences.append(event)
        self._events.extend(differences)
        return tuple(differences)

    def record(self, event: DriftEvent) -> DriftEvent:
        """Record an externally produced drift event without changing it."""
        if any(existing.event_id == event.event_id for existing in self._events):
            raise ValueError(f"drift event already exists: {event.event_id}")
        self._events.append(event)
        return event

    def events(self, entity_id: str | None = None) -> tuple[DriftEvent, ...]:
        """Return drift events ordered by timestamp and identifier."""
        selected = [event for event in self._events if entity_id is None or event.entity_id == entity_id]
        return tuple(sorted(selected, key=lambda event: (event.timestamp, event.event_id)))

    def summary(self) -> dict[str, int]:
        """Return counts by drift status."""
        result: dict[str, int] = {}
        for event in self._events:
            result[event.status] = result.get(event.status, 0) + 1
        return dict(sorted(result.items()))
