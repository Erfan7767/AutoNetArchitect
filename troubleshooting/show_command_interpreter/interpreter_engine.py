"""Generic read-only show-command interpretation engine."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field


class ShowInterpretation(BaseModel):
    """Structured interpretation of one command output."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    vendor: str
    platform: str
    command: str
    parsed_data: dict[str, Any] = Field(default_factory=dict)
    anomalies: list[str] = Field(default_factory=list)
    health_indicators: dict[str, str] = Field(default_factory=dict)
    confidence: float = 0.0
    limitations: list[str] = Field(default_factory=list)

    def model_post_init(self, __context: Any) -> None:
        """Validate confidence."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("interpretation confidence must be between zero and one")


@dataclass(frozen=True)
class InterpreterContext:
    """Context passed to vendor-specific interpreters."""

    vendor: str
    platform: str
    command: str
    raw_output: str


class InterpreterEngine:
    """Interpret common network outputs without claiming vendor completeness."""

    def __init__(self) -> None:
        """Initialize vendor registry."""
        self._interpreters: dict[tuple[str, str], Any] = {}

    def register(self, interpreter: Any) -> None:
        """Register a vendor-specific interpreter instance."""
        key = (str(interpreter.vendor).lower(), str(interpreter.platform).lower())
        self._interpreters[key] = interpreter

    def parse(self, raw_output: str, command: str, vendor: str, platform: str) -> ShowInterpretation:
        """Parse output using a registered interpreter or conservative generic logic."""
        if not isinstance(raw_output, str) or not raw_output.strip():
            raise ValueError("raw_output must be a non-empty string")
        if not self._is_read_only(command):
            raise ValueError("show-command interpreter accepts only read-only commands")
        key = (vendor.lower(), platform.lower())
        interpreter = self._interpreters.get(key)
        if interpreter is not None:
            return interpreter.interpret(raw_output, command)
        return self._generic(raw_output, command, vendor, platform)

    @staticmethod
    def _is_read_only(command: str) -> bool:
        """Reject obvious configuration or destructive commands."""
        forbidden = ("configure", "conf t", "set ", "delete ", "remove ", "reload", "restart", "shutdown", "write", "commit", "clear ")
        return not any(token in command.lower() for token in forbidden)

    @classmethod
    def _generic(cls, raw_output: str, command: str, vendor: str, platform: str) -> ShowInterpretation:
        """Perform conservative generic parsing for common health markers."""
        parsed: dict[str, Any] = {"line_count": len(raw_output.splitlines()), "command": command}
        anomalies: list[str] = []
        indicators: dict[str, str] = {}
        lower = raw_output.lower()
        interface_match = re.search(r"(?im)^\s*([A-Za-z]+[A-Za-z0-9/.-]+)\s+(up|down|administratively down)\s+(up|down)\b", raw_output)
        if interface_match:
            parsed["interface"] = interface_match.group(1)
            parsed["status"] = interface_match.group(2)
            parsed["protocol"] = interface_match.group(3)
            if interface_match.group(2).lower() != "up" or interface_match.group(3).lower() != "up":
                anomalies.append("interface_or_protocol_not_up")
                indicators["interface"] = "degraded"
        if re.search(r"(?i)crc|input errors|output errors|err-disable|errdisabled", raw_output):
            anomalies.append("interface_error_or_errdisable_marker")
            indicators["errors"] = "degraded"
        for state in ("idle", "active", "init", "exstart", "exchange", "loading", "down", "blocked", "denied", "timeout", "failed"):
            if re.search(rf"(?i)\b{re.escape(state)}\b", raw_output):
                anomalies.append(f"state_marker:{state}")
        if re.search(r"(?i)established|full|up/up|synchronized|success", raw_output):
            indicators["operational_state"] = "healthy_or_partially_healthy"
        if anomalies:
            indicators.setdefault("overall", "anomaly_detected")
        else:
            indicators.setdefault("overall", "no_bounded_anomaly_detected")
        evidence_id = f"show:{hashlib.sha256(f'{vendor}|{platform}|{command}|{raw_output}'.encode()).hexdigest()[:16]}"
        confidence = 0.65 if parsed.keys() - {"line_count", "command"} else 0.35
        limitations = ["generic parser used; vendor-specific semantics may require a registered interpreter"]
        return ShowInterpretation(evidence_id=evidence_id, vendor=vendor, platform=platform, command=command, parsed_data=parsed, anomalies=list(dict.fromkeys(anomalies)), health_indicators=indicators, confidence=confidence, limitations=limitations)
