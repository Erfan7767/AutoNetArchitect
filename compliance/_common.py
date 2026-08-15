"""Shared compliance governance helpers."""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from designers.base_designer import Assumption, DecisionRecord


def decision(owner: str, decision_id: str, choice: Any, rationale: str, alternatives: list[Any], rejection_reasons: Mapping[str, str]) -> DecisionRecord:
    """Create an auditable DecisionRecord."""
    return DecisionRecord(owner, decision_id, choice, rationale, alternatives, dict(rejection_reasons))


def assumption(key: str, value: Any, rationale: str, requires_validation: bool = True) -> Assumption:
    """Create an explicit Assumption."""
    return Assumption(key, value, rationale, requires_validation)


def decision_dict(item: DecisionRecord) -> dict[str, Any]:
    """Serialize a DecisionRecord without losing traceability."""
    return {"designer": item.designer, "decision_id": item.decision_id, "choice": item.choice, "rationale": item.rationale, "alternatives": item.alternatives, "rejection_reasons": item.rejection_reasons, "created_at": item.created_at.isoformat()}


def unique(values: Iterable[str]) -> list[str]:
    """Deduplicate identifiers while preserving order."""
    return list(dict.fromkeys(str(value) for value in values if str(value)))


def state_from_evidence(has_authority: bool, supporting: int, contradicting: int, required_domains: set[str], present_domains: set[str]) -> tuple[str, str, list[str]]:
    """Apply conservative evidence state logic."""
    missing = sorted(required_domains - present_domains)
    if contradicting:
        return "failed", "contradictory evidence is present", missing
    if supporting == 0:
        return "not_verifiable_with_current_inputs", "no supporting technical evidence was supplied", missing
    if not has_authority or missing:
        return "partially_verified", "supporting evidence exists but authoritative scope or required evidence domains are incomplete", missing
    return "verified", "supporting evidence covers the declared technical control and required domains", missing
