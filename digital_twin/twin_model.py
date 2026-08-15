"""Digital Twin state contracts with explicit provenance and temporal meaning."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping


class TwinStateKind(str, Enum):
    """Permitted meanings for a twin state snapshot."""

    LOGICAL = "logical_model"
    DEPLOYMENT = "deployment_state"
    DISCOVERED = "discovered_operational_state"
    OPERATIONAL = "operational_state"
    INFERRED_TRANSIENT = "inferred_transient_state"
    HISTORICAL_REPLAY = "replayed_historical_state"


class StateCertainty(str, Enum):
    """Certainty labels that prevent inferred state from becoming fact."""

    OBSERVED = "observed"
    DECLARED = "declared"
    INFERRED = "inferred"
    REPLAYED = "replayed"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class StateProvenance:
    """Evidence and temporal provenance for one state value."""

    source: str
    evidence_ids: tuple[str, ...] = ()
    observed_at: str | None = None
    ingested_at: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    certainty: str = StateCertainty.UNKNOWN.value
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize provenance without discarding uncertainty."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class TwinState:
    """One versioned state payload for an entity or topology."""

    state_id: str
    entity_id: str
    kind: str
    values: dict[str, Any]
    provenance: StateProvenance
    version: int = 1
    state_hash: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize one twin state."""
        return asdict(self) | {"provenance": self.provenance.to_dict()}


@dataclass(frozen=True)
class TwinModel:
    """Composite Digital Twin linking design, deployment, discovered, operational, and historical views."""

    twin_id: str
    created_at: str
    states: tuple[TwinState, ...] = ()
    topology: dict[str, Any] = field(default_factory=dict)
    fidelity_cap: str = "evidence_bounded"
    full_fidelity_claim: bool = False

    def add_state(self, state: TwinState) -> "TwinModel":
        """Return a new model with one state appended immutably."""
        return TwinModel(self.twin_id, self.created_at, self.states + (state,), dict(self.topology), self.fidelity_cap, self.full_fidelity_claim)

    def states_for(self, entity_id: str, kind: str | None = None) -> tuple[TwinState, ...]:
        """Return states for an entity, optionally filtered by state kind."""
        return tuple(state for state in self.states if state.entity_id == entity_id and (kind is None or state.kind == kind))

    def latest(self, entity_id: str, kind: str | None = None) -> TwinState | None:
        """Return the latest versioned state by deterministic version ordering."""
        candidates = self.states_for(entity_id, kind)
        return max(candidates, key=lambda state: (state.version, state.provenance.observed_at or state.provenance.ingested_at or ""), default=None)

    def state_kinds(self) -> tuple[str, ...]:
        """Return distinct state kinds currently represented."""
        return tuple(sorted({state.kind for state in self.states}))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the complete twin model."""
        return {"twin_id": self.twin_id, "created_at": self.created_at, "states": [state.to_dict() for state in self.states], "topology": dict(self.topology), "fidelity_cap": self.fidelity_cap, "full_fidelity_claim": self.full_fidelity_claim}

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TwinModel":
        """Construct a model from an explicit mapping without inferring omitted states."""
        if not value.get("twin_id") or not value.get("created_at"):
            raise ValueError("twin_id and created_at are required")
        states: list[TwinState] = []
        for raw in value.get("states", ()):
            provenance_raw = dict(raw.get("provenance", {}))
            provenance = StateProvenance(str(provenance_raw.get("source", "")), tuple(str(item) for item in provenance_raw.get("evidence_ids", ())), provenance_raw.get("observed_at"), provenance_raw.get("ingested_at"), provenance_raw.get("valid_from"), provenance_raw.get("valid_until"), str(provenance_raw.get("certainty", StateCertainty.UNKNOWN.value)), float(provenance_raw.get("confidence", 0.0)))
            states.append(TwinState(str(raw.get("state_id", "")), str(raw.get("entity_id", "")), str(raw.get("kind", "")), dict(raw.get("values", {})), provenance, int(raw.get("version", 1)), str(raw.get("state_hash", ""))))
        return cls(str(value["twin_id"]), str(value["created_at"]), tuple(states), dict(value.get("topology", {})), str(value.get("fidelity_cap", "evidence_bounded")), bool(value.get("full_fidelity_claim", False)))
