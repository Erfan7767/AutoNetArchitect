"""State ingestion into a provenance-preserving Digital Twin."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Mapping

from .twin_model import StateCertainty, StateProvenance, TwinState, TwinStateKind


class StateIngestor:
    """Ingest explicit state observations and declarations without hidden inference."""

    KIND_ALIASES = {
        "logical": TwinStateKind.LOGICAL.value,
        "logical_model": TwinStateKind.LOGICAL.value,
        "deployment": TwinStateKind.DEPLOYMENT.value,
        "deployment_state": TwinStateKind.DEPLOYMENT.value,
        "discovered": TwinStateKind.DISCOVERED.value,
        "discovered_operational_state": TwinStateKind.DISCOVERED.value,
        "operational": TwinStateKind.OPERATIONAL.value,
        "operational_state": TwinStateKind.OPERATIONAL.value,
        "inferred": TwinStateKind.INFERRED_TRANSIENT.value,
        "inferred_transient": TwinStateKind.INFERRED_TRANSIENT.value,
        "historical": TwinStateKind.HISTORICAL_REPLAY.value,
        "replayed_historical": TwinStateKind.HISTORICAL_REPLAY.value,
    }

    def ingest(
        self,
        entity_id: str,
        kind: str,
        values: Mapping[str, Any],
        *,
        source: str,
        evidence_ids: tuple[str, ...] = (),
        observed_at: str | None = None,
        valid_from: str | None = None,
        valid_until: str | None = None,
        certainty: str | None = None,
        confidence: float = 0.0,
        version: int = 1,
    ) -> TwinState:
        """Create one state with explicit source, certainty, and time fields."""
        normalized_kind = self._normalize_kind(kind)
        if not entity_id or not normalized_kind or not source:
            raise ValueError("entity_id, recognized kind, and source are required")
        if not isinstance(values, Mapping):
            raise TypeError("state values must be a mapping")
        bounded_confidence = max(0.0, min(1.0, float(confidence)))
        normalized_certainty = certainty or self._default_certainty(normalized_kind)
        if normalized_certainty not in {item.value for item in StateCertainty}:
            raise ValueError("certainty must be a supported StateCertainty value")
        provenance = StateProvenance(source, tuple(dict.fromkeys(str(item) for item in evidence_ids)), observed_at, datetime.now(timezone.utc).isoformat(), valid_from, valid_until, normalized_certainty, bounded_confidence)
        state_id = f"state:{entity_id}:{normalized_kind}:{version}"
        state_hash = self._hash({"state_id": state_id, "entity_id": entity_id, "kind": normalized_kind, "values": dict(values), "provenance": provenance.to_dict()})
        return TwinState(state_id, entity_id, normalized_kind, dict(values), provenance, int(version), state_hash)

    @classmethod
    def ingest_mapping(cls, value: Mapping[str, Any]) -> TwinState:
        """Ingest a fully explicit mapping without assigning omitted evidence."""
        provenance = dict(value.get("provenance", {}))
        return cls().ingest(str(value.get("entity_id", "")), str(value.get("kind", "")), dict(value.get("values", {})), source=str(provenance.get("source", value.get("source", ""))), evidence_ids=tuple(str(item) for item in provenance.get("evidence_ids", value.get("evidence_ids", ()))), observed_at=provenance.get("observed_at", value.get("observed_at")), valid_from=provenance.get("valid_from", value.get("valid_from")), valid_until=provenance.get("valid_until", value.get("valid_until")), certainty=provenance.get("certainty", value.get("certainty")), confidence=float(provenance.get("confidence", value.get("confidence", 0.0))), version=int(value.get("version", 1)))

    @classmethod
    def _normalize_kind(cls, kind: str) -> str:
        """Normalize state kind aliases while rejecting unknown categories."""
        return cls.KIND_ALIASES.get(str(kind).strip().lower(), "")

    @staticmethod
    def _default_certainty(kind: str) -> str:
        """Assign only semantic defaults based on state source category."""
        if kind in {TwinStateKind.LOGICAL.value, TwinStateKind.DEPLOYMENT.value}:
            return StateCertainty.DECLARED.value
        if kind in {TwinStateKind.DISCOVERED.value, TwinStateKind.OPERATIONAL.value}:
            return StateCertainty.OBSERVED.value
        if kind == TwinStateKind.INFERRED_TRANSIENT.value:
            return StateCertainty.INFERRED.value
        return StateCertainty.REPLAYED.value

    @staticmethod
    def _hash(value: Mapping[str, Any]) -> str:
        """Hash canonical state content for lineage."""
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()
