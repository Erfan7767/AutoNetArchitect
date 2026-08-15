"""Interface counter analysis with explicit threshold provenance."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field


class InterfaceErrorFinding(BaseModel):
    """One interface error interpretation."""

    model_config = ConfigDict(extra="forbid")

    interface: str
    error_type: str
    count: int | float
    threshold: int | float | None
    severity: str
    likely_causes: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class InterfaceErrorReport(BaseModel):
    """Aggregated interface error report."""

    model_config = ConfigDict(extra="forbid")

    findings: list[InterfaceErrorFinding] = Field(default_factory=list)
    analyzed_interfaces: list[str] = Field(default_factory=list)
    threshold_source: str
    confidence: float
    assumptions: list[str] = Field(default_factory=list)
    decision_id: str


class InterfaceErrorAnalyzer:
    """Analyze explicit counters and never fabricate thresholds."""

    DEFAULT_THRESHOLDS = {"crc": 0, "input_errors": 0, "output_errors": 0, "collisions": 0, "late_collisions": 0, "runts": 0, "giants": 0, "output_drops": 0}
    CAUSES = {
        "crc": ("bad cable", "dirty optical connector", "EMI", "duplex mismatch"),
        "input_errors": ("subtype-specific receive errors", "physical impairment"),
        "output_errors": ("egress impairment", "hardware or queue issue"),
        "output_drops": ("congestion", "QoS shaping", "buffer exhaustion"),
        "collisions": ("half-duplex operation", "hub in path"),
        "late_collisions": ("cable length or duplex mismatch", "physical impairment"),
        "runts": ("collisions", "bad NIC or physical path"),
        "giants": ("MTU mismatch", "unsupported jumbo frames"),
    }

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def analyze(self, counters: Mapping[str, Mapping[str, Any]], *, thresholds: Mapping[str, float] | None = None, evidence_ids: Mapping[str, list[str]] | None = None) -> InterfaceErrorReport:
        """Analyze per-interface counters against supplied or conservative zero thresholds."""
        active_thresholds = dict(thresholds or self.DEFAULT_THRESHOLDS)
        threshold_source = "supplied_thresholds" if thresholds is not None else "bounded_zero_counter_baseline"
        if thresholds is None:
            self.assumptions.append(Assumption("interface_error_thresholds", "bounded_zero_counter_baseline", "no external threshold file was supplied; any non-zero counter is flagged, not diagnosed", True))
        findings: list[InterfaceErrorFinding] = []
        for interface, values in counters.items():
            for error_type, raw_count in values.items():
                if error_type not in active_thresholds:
                    continue
                try:
                    count = float(raw_count)
                except (TypeError, ValueError):
                    self.assumptions.append(Assumption(f"counter:{interface}:{error_type}", "unparseable", "the counter is not converted into an invented numeric value", True))
                    continue
                threshold = active_thresholds[error_type]
                if count <= threshold:
                    continue
                severity = "high" if error_type in {"crc", "late_collisions", "output_drops"} else "medium"
                ids = list((evidence_ids or {}).get(interface, []))
                findings.append(InterfaceErrorFinding(interface=interface, error_type=error_type, count=int(count) if count.is_integer() else count, threshold=threshold, severity=severity, likely_causes=list(self.CAUSES.get(error_type, ("cause requires additional evidence",))), recommended_checks=[f"inspect {error_type} trend", "validate physical, QoS, and duplex evidence"], evidence_ids=ids))
        confidence = 0.85 if counters else 0.0
        decision = DecisionRecord("InterfaceErrorAnalyzer", "interface-error-analysis", "threshold_comparison", "compare supplied counters to explicit thresholds and report likely causes as hypotheses", ["threshold_comparison", "automatic_root_cause"], {"threshold_comparison": "selected", "automatic_root_cause": "not allowed without corroborating evidence"})
        self.decisions.append(decision)
        return InterfaceErrorReport(findings=findings, analyzed_interfaces=list(counters.keys()), threshold_source=threshold_source, confidence=confidence, assumptions=[item.key for item in self.assumptions], decision_id=decision.decision_id)
