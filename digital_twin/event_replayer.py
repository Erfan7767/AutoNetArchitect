"""Historical event replay for Digital Twin state reconstruction."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .state_ingestor import StateIngestor
from .twin_model import StateCertainty, StateProvenance, TwinState, TwinStateKind


@dataclass(frozen=True)
class TwinEvent:
    """One timestamped event eligible for deterministic replay."""

    event_id: str
    timestamp: str
    entity_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class ReplayResult:
    """Result of replaying a bounded historical event sequence."""

    status: str
    as_of: str | None
    states: tuple[TwinState, ...]
    applied_event_ids: tuple[str, ...]
    skipped_event_ids: tuple[str, ...]
    assumptions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize replay output with historical provenance intact."""
        return {"status": self.status, "as_of": self.as_of, "states": [state.to_dict() for state in self.states], "applied_event_ids": list(self.applied_event_ids), "skipped_event_ids": list(self.skipped_event_ids), "assumptions": list(self.assumptions)}


class EventReplayer:
    """Replay known event types into historical state without claiming live truth."""

    SUPPORTED_EVENTS = {"state_update", "merge_state", "remove_field"}

    def replay(self, base_states: Mapping[str, TwinState], events: Sequence[TwinEvent | Mapping[str, Any]], as_of: str | None = None) -> ReplayResult:
        """Reconstruct historical states from base state and ordered events."""
        current = {str(entity_id): state for entity_id, state in base_states.items()}
        normalized = [self._normalize_event(event) for event in events]
        normalized.sort(key=lambda item: (item.timestamp, item.event_id))
        applied: list[str] = []
        skipped: list[str] = []
        assumptions: list[str] = ["replay reconstructs state from supplied events and does not assert unobserved intermediate values"]
        for event in normalized:
            if as_of is not None and event.timestamp > as_of:
                continue
            if event.event_type not in self.SUPPORTED_EVENTS or event.entity_id not in current:
                skipped.append(event.event_id)
                assumptions.append(f"event {event.event_id} was not replayed because its type or base entity is unavailable")
                continue
            previous = current[event.entity_id]
            values = dict(previous.values)
            if event.event_type in {"state_update", "merge_state"}:
                values.update(event.payload)
            else:
                for key in event.payload.get("fields", ()):
                    values.pop(str(key), None)
            provenance = StateProvenance("event_replay", event.evidence_ids, event.timestamp, event.timestamp, event.timestamp, as_of, StateCertainty.REPLAYED.value, min(previous.provenance.confidence, 0.85))
            state_id = f"replay:{event.event_id}:{event.entity_id}"
            state_hash = StateIngestor._hash({"state_id": state_id, "entity_id": event.entity_id, "kind": TwinStateKind.HISTORICAL_REPLAY.value, "values": values, "provenance": provenance.to_dict()})
            current[event.entity_id] = TwinState(state_id, event.entity_id, TwinStateKind.HISTORICAL_REPLAY.value, values, provenance, previous.version + 1, state_hash)
            applied.append(event.event_id)
        status = "replayed" if applied or not events else "not_verifiable_with_current_inputs"
        return ReplayResult(status, as_of, tuple(sorted(current.values(), key=lambda state: state.entity_id)), tuple(applied), tuple(skipped), tuple(dict.fromkeys(assumptions)))

    @staticmethod
    def _normalize_event(event: TwinEvent | Mapping[str, Any]) -> TwinEvent:
        """Normalize one explicit event without inferring timestamp or identity."""
        if isinstance(event, TwinEvent):
            return event
        if not isinstance(event, Mapping):
            raise TypeError("event must be TwinEvent or mapping")
        return TwinEvent(str(event.get("event_id", "")), str(event.get("timestamp", "")), str(event.get("entity_id", "")), str(event.get("event_type", "")), dict(event.get("payload", {})), tuple(str(item) for item in event.get("evidence_ids", ())))
