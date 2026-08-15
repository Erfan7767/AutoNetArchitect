"""Read-only automatic incident detection rule evaluation."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field

from ._common import make_assumption, make_decision
from .incident_models import IncidentCategory, IncidentSeverity


class DetectionRule(BaseModel):
    """Declarative rule for incident detection."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    rule_name: str
    rule_type: str
    condition: dict[str, Any]
    severity_assignment: IncidentSeverity
    category: IncidentCategory
    auto_create_incident: bool = False
    notification_targets: list[str] = Field(default_factory=list)
    suppression_window_minutes: int = 0
    correlation_group: str = ""


class DetectionResult(BaseModel):
    """Rule evaluation result."""

    model_config = ConfigDict(extra="forbid")

    rule_id: str
    matched: bool
    reason: str
    incident_creation_allowed: bool
    severity: IncidentSeverity
    category: IncidentCategory
    notification_targets: list[str] = Field(default_factory=list)
    correlation_group: str = ""
    assumptions: list[str] = Field(default_factory=list)
    decision_id: str


class AutoDetectionRules:
    """Evaluate validated detection rules against explicit monitoring signals."""

    def __init__(self, rules: Sequence[DetectionRule] = ()) -> None:
        """Initialize rule registry."""
        self.rules = {rule.rule_id: rule for rule in rules}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def add(self, rule: DetectionRule) -> None:
        """Add or replace one rule explicitly."""
        self.rules[rule.rule_id] = rule

    def evaluate(self, rule_id: str, signal: Mapping[str, Any]) -> DetectionResult:
        """Evaluate one rule against a signal mapping."""
        rule = self.rules.get(rule_id)
        if rule is None:
            raise KeyError(f"unknown detection rule: {rule_id}")
        matched, reason = self._match(rule, signal)
        if not signal:
            self.assumptions.append(make_assumption(f"detection:{rule_id}:signal", "empty", "empty monitoring input cannot match a rule", True))
        decision = make_decision("AutoDetectionRules", f"detection:{rule_id}", matched, "evaluate only explicit signal fields against the rule condition", [True, False], {str(item): "not selected by supplied signal" for item in [True, False] if item != matched})
        self.decisions.append(decision)
        return DetectionResult(rule_id=rule_id, matched=matched, reason=reason, incident_creation_allowed=matched and rule.auto_create_incident, severity=rule.severity_assignment, category=rule.category, notification_targets=list(rule.notification_targets), correlation_group=rule.correlation_group, assumptions=[item.key for item in self.assumptions], decision_id=decision.decision_id)

    def evaluate_all(self, signal: Mapping[str, Any]) -> list[DetectionResult]:
        """Evaluate all registered rules in stable order."""
        return [self.evaluate(rule_id, signal) for rule_id in sorted(self.rules)]

    @staticmethod
    def _match(rule: DetectionRule, signal: Mapping[str, Any]) -> tuple[bool, str]:
        """Match threshold, state, pattern, absence, or composite conditions."""
        condition = rule.condition
        if rule.rule_type == "threshold_rule":
            value = signal.get(str(condition.get("metric", "")))
            threshold = condition.get("threshold")
            operator = str(condition.get("operator", ">"))
            if value is None or threshold is None:
                return False, "required threshold signal is missing"
            matched = {">": value > threshold, ">=": value >= threshold, "<": value < threshold, "<=": value <= threshold, "==": value == threshold}.get(operator, False)
            return bool(matched), f"metric={value} operator={operator} threshold={threshold}"
        if rule.rule_type == "state_change_rule":
            expected = condition.get("state")
            actual = signal.get(str(condition.get("field", "state")))
            return actual == expected, f"state={actual} expected={expected}"
        if rule.rule_type == "pattern_rule":
            pattern = str(condition.get("pattern", "")).lower()
            text = str(signal.get(str(condition.get("field", "message")), "")).lower()
            return bool(pattern and pattern in text), f"pattern={pattern} present={pattern in text}"
        if rule.rule_type == "absence_rule":
            field = str(condition.get("field", "signal"))
            absent = signal.get(field) is None or signal.get(field) is False
            return absent, f"field={field} absent={absent}"
        if rule.rule_type == "composite_rule":
            clauses = condition.get("clauses", [])
            matched = all(bool(clause.get("field") in signal and signal.get(str(clause.get("field"))) == clause.get("equals")) for clause in clauses if isinstance(clause, Mapping))
            return matched, f"composite clauses matched={matched}"
        return False, "unsupported rule type"
