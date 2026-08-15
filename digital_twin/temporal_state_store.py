"""Versioned temporal storage for Digital Twin states and snapshots."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from .twin_model import TwinState


@dataclass(frozen=True)
class TemporalSnapshot:
    """Immutable time-indexed collection of states."""

    snapshot_id: str
    timestamp: str
    states: tuple[TwinState, ...]
    source_event_ids: tuple[str, ...] = ()
    replayed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Serialize snapshot content."""
        return {"snapshot_id": self.snapshot_id, "timestamp": self.timestamp, "states": [state.to_dict() for state in self.states], "source_event_ids": list(self.source_event_ids), "replayed": self.replayed}


class TemporalStateStore:
    """In-memory immutable-by-replacement temporal store for V1."""

    def __init__(self) -> None:
        """Create an empty temporal state store."""
        self._states: dict[str, list[TwinState]] = {}
        self._snapshots: dict[str, TemporalSnapshot] = {}

    def append(self, state: TwinState) -> TwinState:
        """Append a state version without mutating previous versions."""
        versions = self._states.setdefault(state.entity_id, [])
        if any(item.state_id == state.state_id for item in versions):
            raise ValueError(f"state version already exists: {state.state_id}")
        if versions and state.version <= max(item.version for item in versions):
            raise ValueError("state version must increase monotonically for an entity")
        versions.append(state)
        return state

    def snapshot(self, snapshot_id: str, timestamp: str, states: Iterable[TwinState], source_event_ids: tuple[str, ...] = (), replayed: bool = False) -> TemporalSnapshot:
        """Create and retain a deterministic snapshot from supplied state versions."""
        if not snapshot_id or not timestamp:
            raise ValueError("snapshot_id and timestamp are required")
        if snapshot_id in self._snapshots:
            raise ValueError(f"snapshot already exists: {snapshot_id}")
        selected = tuple(states)
        for state in selected:
            if not any(existing.state_id == state.state_id for existing in self._states.get(state.entity_id, ())):
                self.append(state)
        result = TemporalSnapshot(snapshot_id, timestamp, selected, tuple(dict.fromkeys(source_event_ids)), replayed)
        self._snapshots[snapshot_id] = result
        return result

    def history(self, entity_id: str, kind: str | None = None) -> tuple[TwinState, ...]:
        """Return ordered state history for one entity."""
        return tuple(state for state in self._states.get(entity_id, ()) if kind is None or state.kind == kind)

    def at(self, entity_id: str, timestamp: str, kind: str | None = None) -> TwinState | None:
        """Return the latest known state at or before a timestamp."""
        candidates = [state for state in self.history(entity_id, kind) if (state.provenance.observed_at or state.provenance.valid_from or state.provenance.ingested_at or "") <= timestamp]
        return max(candidates, key=lambda state: (state.version, state.provenance.observed_at or state.provenance.valid_from or state.provenance.ingested_at or ""), default=None)

    def snapshots(self) -> tuple[TemporalSnapshot, ...]:
        """Return snapshots ordered by timestamp and identifier."""
        return tuple(sorted(self._snapshots.values(), key=lambda item: (item.timestamp, item.snapshot_id)))

    def snapshot_by_id(self, snapshot_id: str) -> TemporalSnapshot | None:
        """Return one snapshot or None if it is not retained."""
        return self._snapshots.get(snapshot_id)

    def state_count(self) -> int:
        """Return total retained state versions."""
        return sum(len(items) for items in self._states.values())
