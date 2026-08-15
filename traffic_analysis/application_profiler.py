"""Application bandwidth and QoS profiles."""
from __future__ import annotations
from typing import Any, Mapping
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import ApplicationProfile, TrafficPriorityClass, TrafficSource

class ApplicationProfiler:
    """Build profiles from data assets or human-supplied custom definitions."""
    DEFAULTS = {"web": ("tcp", 443, 0.5, 2.0, "latency_sensitive", "loss_tolerant", "jitter_tolerant", TrafficPriorityClass.DEFAULT), "voice": ("udp", 5060, 0.08, 0.12, "latency_critical", "loss_sensitive", "jitter_sensitive", TrafficPriorityClass.REAL_TIME), "video": ("udp", 5004, 2.0, 8.0, "latency_critical", "loss_sensitive", "jitter_sensitive", TrafficPriorityClass.REAL_TIME), "database": ("tcp", 3306, 1.0, 5.0, "latency_sensitive", "loss_tolerant", "jitter_tolerant", TrafficPriorityClass.BUSINESS_CRITICAL), "backup": ("tcp", 443, 5.0, 20.0, "latency_tolerant", "loss_tolerant", "jitter_tolerant", TrafficPriorityClass.SCAVENGER)}
    def __init__(self, profiles: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        """Initialize application profile catalog."""
        self.profiles = {key: dict(value) for key, value in (profiles or {}).items()}
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def profile(self, *, application_name: str, concurrent_sessions: int | None = None, custom: Mapping[str, Any] | None = None, human_supplied: bool = False) -> ApplicationProfile:
        """Create one application profile."""
        data = dict(custom or self.profiles.get(application_name, {}))
        if custom and not human_supplied:
            raise ValueError("custom application profile is HumanSuppliedMandatory")
        default = self.DEFAULTS.get(application_name)
        if not data and default is None:
            self.assumptions.append(make_assumption(f"application:{application_name}", "unknown", "no default or human-supplied application profile exists", True))
            return ApplicationProfile(application_name=application_name, protocol="unknown", latency_sensitivity="unknown", loss_sensitivity="unknown", jitter_sensitivity="unknown", qos_class_mapping=TrafficPriorityClass.DEFAULT, source=TrafficSource.ESTIMATED, assumptions=[item.key for item in self.assumptions])
        if default is not None:
            protocol, port, avg, peak, latency, loss, jitter, qos = default
        else:
            protocol, port, avg, peak, latency, loss, jitter, qos = (str(data.get("protocol", "unknown")), data.get("port"), data.get("avg_session_bandwidth_mbps"), data.get("peak_session_bandwidth_mbps"), str(data.get("latency_sensitivity", "unknown")), str(data.get("loss_sensitivity", "unknown")), str(data.get("jitter_sensitivity", "unknown")), TrafficPriorityClass(data.get("qos_class_mapping", "default")))
        avg = data.get("avg_session_bandwidth_mbps", avg)
        peak = data.get("peak_session_bandwidth_mbps", peak)
        total = float(peak) * concurrent_sessions if peak is not None and concurrent_sessions is not None else None
        if concurrent_sessions is None:
            self.assumptions.append(make_assumption(f"application:{application_name}:sessions", "unknown", "total application bandwidth cannot be calculated without concurrent sessions", True))
        source = TrafficSource.HUMAN_SUPPLIED if custom else TrafficSource.ESTIMATED
        evidence = [str(data["evidence_id"])] if data.get("evidence_id") else []
        decision = make_decision("ApplicationProfiler", f"application:{application_name}", "validated_profile", "use a default profile or explicitly human-supplied custom profile", ["validated_profile", "invent_application_behavior"], {"validated_profile": "selected", "invent_application_behavior": "rejected"})
        self.decisions.append(decision)
        return ApplicationProfile(application_name=application_name, protocol=protocol, port=port, avg_session_bandwidth_mbps=avg, peak_session_bandwidth_mbps=peak, concurrent_sessions_estimate=concurrent_sessions, total_bandwidth_estimate_mbps=total, latency_sensitivity=latency, loss_sensitivity=loss, jitter_sensitivity=jitter, qos_class_mapping=qos, source=source, evidence_ids=evidence, assumptions=[item.key for item in self.assumptions])
