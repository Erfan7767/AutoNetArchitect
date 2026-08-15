"""Classification of transient operational states without elevating inference to fact."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Sequence

from .twin_model import StateCertainty, TwinStateKind


@dataclass(frozen=True)
class TransientClassification:
    """Classification result for a possibly unstable state."""

    entity_id: str
    label: str
    state_kind: str
    certainty: str
    confidence: float
    previous_state: Any = None
    current_state: Any = None
    stability_observations: int = 0
    required_stability_observations: int = 0
    observed_at: str | None = None
    valid_until: str | None = None
    evidence_ids: tuple[str, ...] = ()
    rationale: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize transient classification."""
        return asdict(self) | {"evidence_ids": list(self.evidence_ids)}


class TransientStateClassifier:
    """Classify observed transitions and short-lived states conservatively."""

    def classify(
        self,
        entity_id: str,
        previous: Mapping[str, Any] | None,
        current: Mapping[str, Any] | None,
        *,
        stability_observations: int = 0,
        required_stability_observations: int = 2,
        observed_at: str | None = None,
        valid_until: str | None = None,
        evidence_ids: Sequence[str] = (),
    ) -> TransientClassification:
        """Classify current state using explicit transition and stability evidence."""
        if not entity_id:
            raise ValueError("entity_id is required")
        ids = tuple(dict.fromkeys(str(item) for item in evidence_ids))
        if current is None:
            return TransientClassification(entity_id, "unknown", TwinStateKind.INFERRED_TRANSIENT.value, StateCertainty.UNKNOWN.value, 0.0, previous_state=(previous or {}).get("state"), stability_observations=stability_observations, required_stability_observations=required_stability_observations, observed_at=observed_at, valid_until=valid_until, evidence_ids=ids, rationale="current state observation is missing")
        previous_state = (previous or {}).get("state")
        current_state = current.get("state")
        if current_state in (None, ""):
            return TransientClassification(entity_id, "unknown", TwinStateKind.INFERRED_TRANSIENT.value, StateCertainty.UNKNOWN.value, 0.0, previous_state, current_state, stability_observations, required_stability_observations, observed_at, valid_until, ids, "current observation has no explicit state")
        if previous_state != current_state and stability_observations < required_stability_observations:
            confidence = 0.55 if ids else 0.4
            return TransientClassification(entity_id, "transient_change", TwinStateKind.INFERRED_TRANSIENT.value, StateCertainty.INFERRED.value, confidence, previous_state, current_state, stability_observations, required_stability_observations, observed_at, valid_until, ids, "state changed and stability evidence is below the declared threshold")
        if stability_observations >= required_stability_observations:
            return TransientClassification(entity_id, "stable_observed", TwinStateKind.OPERATIONAL.value, StateCertainty.OBSERVED.value, 0.85 if ids else 0.7, previous_state, current_state, stability_observations, required_stability_observations, observed_at, valid_until, ids, "state remained consistent for the declared observation count")
        return TransientClassification(entity_id, "observed_unclassified", TwinStateKind.OPERATIONAL.value, StateCertainty.OBSERVED.value, 0.6 if ids else 0.45, previous_state, current_state, stability_observations, required_stability_observations, observed_at, valid_until, ids, "explicit current state exists but stability evidence is incomplete")
