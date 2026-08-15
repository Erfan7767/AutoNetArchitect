"""Conservative protocol state estimation with observed/inferred separation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence

from .twin_model import StateCertainty


@dataclass(frozen=True)
class ProtocolStateEstimate:
    """One protocol state estimate with explicit certainty and evidence basis."""

    entity_id: str
    protocol: str
    state: str
    certainty: str
    confidence: float
    observed_fields: tuple[str, ...] = ()
    inference_rule: str = ""
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ("state estimate is not protocol emulation",)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the estimate."""
        return asdict(self) | {"observed_fields": list(self.observed_fields), "evidence_ids": list(self.evidence_ids), "limitations": list(self.limitations)}


class ProtocolStateEstimator:
    """Estimate protocol states from explicit observations and declared rules.

    This component does not execute protocol state machines or infer unobserved
    timers, packets, or vendor-specific transitions.
    """

    def estimate(
        self,
        entity_id: str,
        protocol: str,
        observations: Mapping[str, Any] | None,
        *,
        inference_rules: Mapping[str, Mapping[str, Any]] | None = None,
        evidence_ids: Sequence[str] = (),
    ) -> ProtocolStateEstimate:
        """Return observed state when explicit, otherwise a bounded rule estimate."""
        values = dict(observations or {})
        ids = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if not entity_id or not protocol:
            raise ValueError("entity_id and protocol are required")
        explicit = values.get("protocol_state", values.get("state"))
        if explicit not in (None, ""):
            fields = tuple(sorted(str(key) for key in values if key in {"protocol_state", "state", "neighbor_state", "session_state", "keepalive", "last_change"}))
            return ProtocolStateEstimate(entity_id, protocol, str(explicit), StateCertainty.OBSERVED.value, 0.95 if ids else 0.8, fields, "explicit_observation", ids)
        matches = [rule_name for rule_name, conditions in (inference_rules or {}).items() if isinstance(conditions, Mapping) and all(values.get(key) == expected for key, expected in conditions.items())]
        if len(matches) == 1:
            return ProtocolStateEstimate(entity_id, protocol, matches[0], StateCertainty.INFERRED.value, 0.65 if ids else 0.55, tuple(sorted(str(key) for key in values)), f"rule:{matches[0]}", ids)
        if len(matches) > 1:
            return ProtocolStateEstimate(entity_id, protocol, "ambiguous", StateCertainty.AMBIGUOUS.value, 0.2, tuple(sorted(str(key) for key in values)), "multiple_rules_matched", ids)
        return ProtocolStateEstimate(entity_id, protocol, "unknown", StateCertainty.UNKNOWN.value, 0.0, tuple(sorted(str(key) for key in values)), "", ids)

    def estimate_many(self, items: Sequence[Mapping[str, Any]]) -> tuple[ProtocolStateEstimate, ...]:
        """Estimate multiple explicitly described protocol observations."""
        results: list[ProtocolStateEstimate] = []
        for item in items:
            results.append(self.estimate(str(item.get("entity_id", "")), str(item.get("protocol", "")), item.get("observations", {}), inference_rules=item.get("inference_rules", {}), evidence_ids=tuple(str(value) for value in item.get("evidence_ids", ()))))
        return tuple(results)
