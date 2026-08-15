"""Shared governance helpers for Incident Response Engine modules."""

from __future__ import annotations

from typing import Any

from designers.base_designer import Assumption, DecisionRecord
from log_redaction.redacting_filter import RedactingFilter


def make_decision(owner: str, decision_id: str, choice: Any, rationale: str, alternatives: list[Any], rejection_reasons: dict[str, str]) -> DecisionRecord:
    """Create one auditable DecisionRecord."""
    return DecisionRecord(owner, decision_id, choice, rationale, alternatives, rejection_reasons)


def make_assumption(key: str, value: Any, rationale: str, requires_validation: bool = True) -> Assumption:
    """Create one explicit Assumption."""
    return Assumption(key, value, rationale, requires_validation)


def safe_details(details: Any) -> Any:
    """Redact secrets before storing incident details or exporting artifacts."""
    return RedactingFilter.sanitize_value(details)


def decision_dict(decision: DecisionRecord) -> dict[str, Any]:
    """Serialize a DecisionRecord without exposing implementation objects."""
    return {"designer": decision.designer, "decision_id": decision.decision_id, "choice": safe_details(decision.choice), "rationale": decision.rationale, "alternatives": safe_details(decision.alternatives), "rejection_reasons": safe_details(decision.rejection_reasons), "created_at": decision.created_at.isoformat()}


def assumption_dict(assumption: Assumption) -> dict[str, Any]:
    """Serialize an Assumption."""
    return {"key": assumption.key, "value": safe_details(assumption.value), "rationale": assumption.rationale, "requires_validation": assumption.requires_validation}
