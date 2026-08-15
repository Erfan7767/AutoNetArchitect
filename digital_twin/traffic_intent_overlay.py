"""Overlay intended traffic flows against time-scoped observed or inferred state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Sequence

from .twin_model import StateCertainty


class OverlayStatus(str, Enum):
    """Comparison results for traffic intent overlays."""

    MATCHED_OBSERVED = "matched_observed"
    MISMATCH_OBSERVED = "mismatch_observed"
    MATCHED_INFERRED = "matched_inferred"
    MISMATCH_INFERRED = "mismatch_inferred"
    NOT_VERIFIABLE = "not_verifiable_with_current_inputs"


@dataclass(frozen=True)
class TrafficIntent:
    """Declared intended flow and expected state."""

    intent_id: str
    source: str
    destination: str
    expected: str
    protocol: str = ""
    evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Serialize traffic intent."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


@dataclass(frozen=True)
class TrafficOverlayResult:
    """One intent-to-reality comparison with state certainty."""

    intent_id: str
    status: str
    expected: str
    observed: str | None
    certainty: str
    timestamp: str | None
    evidence_ids: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize one overlay result."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


class TrafficIntentOverlay:
    """Compare declared traffic intent with explicit observed state values."""

    def compare(
        self,
        intents: Sequence[TrafficIntent | Mapping[str, Any]],
        observed_states: Mapping[str, Mapping[str, Any]],
    ) -> tuple[TrafficOverlayResult, ...]:
        """Return a result for every declared intent without filling missing observations."""
        results: list[TrafficOverlayResult] = []
        for raw_intent in intents:
            intent = self._normalize_intent(raw_intent)
            observed = observed_states.get(intent.intent_id)
            if not isinstance(observed, Mapping):
                results.append(TrafficOverlayResult(intent.intent_id, OverlayStatus.NOT_VERIFIABLE.value, intent.expected, None, StateCertainty.UNKNOWN.value, None, intent.evidence_ids, "no observed or inferred state was supplied"))
                continue
            observed_value = observed.get("observed", observed.get("state"))
            certainty = str(observed.get("certainty", StateCertainty.UNKNOWN.value))
            timestamp = observed.get("timestamp", observed.get("observed_at"))
            evidence = tuple(dict.fromkeys(intent.evidence_ids + tuple(str(item) for item in observed.get("evidence_ids", ()))))
            if observed_value in (None, "") or certainty == StateCertainty.UNKNOWN.value:
                results.append(TrafficOverlayResult(intent.intent_id, OverlayStatus.NOT_VERIFIABLE.value, intent.expected, None if observed_value in (None, "") else str(observed_value), certainty, timestamp, evidence, "observed state is missing or unknown"))
                continue
            matches = str(observed_value).lower() == intent.expected.lower()
            observed_certainty = StateCertainty.OBSERVED.value if certainty == StateCertainty.OBSERVED.value else StateCertainty.INFERRED.value if certainty == StateCertainty.INFERRED.value else certainty
            if observed_certainty == StateCertainty.OBSERVED.value:
                status = OverlayStatus.MATCHED_OBSERVED.value if matches else OverlayStatus.MISMATCH_OBSERVED.value
            else:
                status = OverlayStatus.MATCHED_INFERRED.value if matches else OverlayStatus.MISMATCH_INFERRED.value
            results.append(TrafficOverlayResult(intent.intent_id, status, intent.expected, str(observed_value), observed_certainty, str(timestamp) if timestamp is not None else None, evidence, "observed value agrees with intent" if matches else "observed value differs from intent"))
        return tuple(results)

    @staticmethod
    def _normalize_intent(value: TrafficIntent | Mapping[str, Any]) -> TrafficIntent:
        """Normalize one explicit intent."""
        if isinstance(value, TrafficIntent):
            return value
        if not isinstance(value, Mapping):
            raise TypeError("traffic intent must be TrafficIntent or mapping")
        return TrafficIntent(str(value.get("intent_id", "")), str(value.get("source", "")), str(value.get("destination", "")), str(value.get("expected", "")), str(value.get("protocol", "")), tuple(str(item) for item in value.get("evidence_ids", ())))
