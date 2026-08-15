"""Shared governance and calculation helpers for Traffic Analysis."""

from __future__ import annotations

from statistics import mean, median, stdev
from typing import Any, Iterable, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord


def make_decision(owner: str, decision_id: str, choice: Any, rationale: str, alternatives: list[Any], rejection_reasons: Mapping[str, str]) -> DecisionRecord:
    """Create an auditable engineering decision."""
    return DecisionRecord(owner, decision_id, choice, rationale, alternatives, dict(rejection_reasons))


def make_assumption(key: str, value: Any, rationale: str, requires_validation: bool = True) -> Assumption:
    """Create an explicit assumption."""
    return Assumption(key, value, rationale, requires_validation)


def decision_dict(decision: DecisionRecord) -> dict[str, Any]:
    """Serialize a DecisionRecord."""
    return {"designer": decision.designer, "decision_id": decision.decision_id, "choice": decision.choice, "rationale": decision.rationale, "alternatives": decision.alternatives, "rejection_reasons": decision.rejection_reasons, "created_at": decision.created_at.isoformat()}


def assumption_dict(assumption: Assumption) -> dict[str, Any]:
    """Serialize an Assumption."""
    return {"key": assumption.key, "value": assumption.value, "rationale": assumption.rationale, "requires_validation": assumption.requires_validation}


def percentile(values: Sequence[float], fraction: float) -> float | None:
    """Calculate a linear-interpolated percentile without inventing values for an empty set."""
    if not values:
        return None
    ordered = sorted(float(value) for value in values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def statistics(values: Sequence[float]) -> dict[str, float | None]:
    """Return baseline statistics for explicit measurements."""
    if not values:
        return {"average": None, "median": None, "percentile_95": None, "standard_deviation": None, "minimum": None, "maximum": None}
    numbers = [float(value) for value in values]
    return {"average": mean(numbers), "median": median(numbers), "percentile_95": percentile(numbers, 0.95), "standard_deviation": stdev(numbers) if len(numbers) > 1 else 0.0, "minimum": min(numbers), "maximum": max(numbers)}


def normalize_mapping(value: Mapping[str, Any] | None) -> dict[str, Any]:
    """Copy a mapping without adding absent facts."""
    return dict(value or {})


def unique(values: Iterable[str]) -> list[str]:
    """Preserve first occurrence order while deduplicating identifiers."""
    return list(dict.fromkeys(str(value) for value in values if str(value)))
