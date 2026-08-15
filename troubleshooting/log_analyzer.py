"""Syslog and event-log analysis for troubleshooting correlation."""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Iterable

from designers.base_designer import Assumption, DecisionRecord
from pydantic import BaseModel, ConfigDict, Field


class LogEvent(BaseModel):
    """Normalized log event."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    timestamp: datetime | None = None
    device_id: str = ""
    severity: str = "unknown"
    code: str = ""
    message: str
    related_target: str = ""
    evidence_id: str = ""


class LogAnalysisReport(BaseModel):
    """Log timeline and bounded pattern findings."""

    model_config = ConfigDict(extra="forbid")

    events: list[LogEvent] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    timeline_ordered: bool
    correlated_groups: list[list[str]] = Field(default_factory=list)
    confidence: float
    assumptions: list[str] = Field(default_factory=list)
    decision_id: str


class LogAnalyzer:
    """Parse common event codes and preserve unknown log content as evidence."""

    PATTERNS = {
        "%LINEPROTO-5-UPDOWN": "interface protocol state change",
        "%SYS-5-RELOAD": "device reload",
        "%OSPF-5-ADJCHG": "OSPF adjacency change",
        "%BGP-5-ADJCHANGE": "BGP adjacency change",
        "%STP-W-PORTSTATUS": "STP port state change",
        "%PM-4-ERR_DISABLE": "port errdisable",
        "%DOT1X-5-FAIL": "802.1X authentication failure",
        "%LINK-3-UPDOWN": "link state change",
        "%DUAL-5-NBRCHANGE": "EIGRP neighbor change",
        "%HSRP-5-STATECHANGE": "HSRP state change",
    }

    def __init__(self) -> None:
        """Initialize decision and assumption registries."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []

    def analyze(self, lines: Iterable[str], *, device_id: str = "", evidence_id_prefix: str = "log") -> LogAnalysisReport:
        """Parse supplied log lines and order events by explicit timestamps when present."""
        events: list[LogEvent] = []
        patterns: list[str] = []
        for index, line in enumerate(lines, start=1):
            text = str(line).strip()
            if not text:
                continue
            code = next((key for key in self.PATTERNS if key in text), "")
            if code:
                patterns.append(self.PATTERNS[code])
            timestamp = self._timestamp(text)
            severity = self._severity(text)
            events.append(LogEvent(event_id=f"{evidence_id_prefix}:{index}", timestamp=timestamp, device_id=device_id, severity=severity, code=code, message=text, evidence_id=f"{evidence_id_prefix}:{index}"))
        if not any(item.timestamp for item in events):
            self.assumptions.append(Assumption("log_timestamps", "not_supplied", "event ordering follows input order because timestamps were absent", True))
        ordered = sorted(events, key=lambda item: item.timestamp or datetime.min.replace(tzinfo=timezone.utc))
        groups: list[list[str]] = []
        for event in ordered:
            if event.timestamp is None:
                continue
            related = [other.event_id for other in ordered if other.timestamp is not None and abs((event.timestamp - other.timestamp).total_seconds()) <= 60]
            if len(related) > 1 and related not in groups:
                groups.append(related)
        decision = DecisionRecord("LogAnalyzer", "log-analysis", "pattern_and_timeline_analysis", "extract explicit codes and timestamps without treating patterns as causal proof", ["pattern_and_timeline_analysis", "automatic_causality"], {"pattern_and_timeline_analysis": "selected", "automatic_causality": "not allowed without corroboration"})
        self.decisions.append(decision)
        return LogAnalysisReport(events=ordered, patterns=list(dict.fromkeys(patterns)), timeline_ordered=bool(events), correlated_groups=groups, confidence=0.85 if events else 0.0, assumptions=[item.key for item in self.assumptions], decision_id=decision.decision_id)

    @staticmethod
    def _timestamp(line: str) -> datetime | None:
        """Parse common ISO or month-day time prefixes."""
        iso = re.search(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)", line)
        if iso:
            try:
                return datetime.fromisoformat(iso.group(1).replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    @staticmethod
    def _severity(line: str) -> str:
        """Infer only explicit severity markers."""
        lower = line.lower()
        for value in ("critical", "error", "warning", "notice", "info"):
            if value in lower:
                return value
        return "unknown"
