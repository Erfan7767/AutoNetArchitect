"""Statistical traffic anomaly detection."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import AnomalyType, BaselineStatistics, FindingSeverity, TrafficAnomaly

class AnomalyDetector:
    """Detect deviations from explicit baselines without claiming causality."""
    def __init__(self) -> None:
        """Initialize anomaly state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def detect(self, *, subject_id: str, metric: str, baseline: BaselineStatistics | None, current_value: float, detected_at: datetime | None = None, rate_of_change: float | None = None, protocol: str | None = None, expected_protocols: Sequence[str] = ()) -> list[TrafficAnomaly]:
        """Return anomalies supported by a baseline, rate, or protocol observation."""
        anomalies: list[TrafficAnomaly] = []
        now = detected_at or datetime.now(timezone.utc)
        if baseline is None or baseline.average is None:
            self.assumptions.append(make_assumption(f"anomaly:{subject_id}:{metric}:baseline", "missing", "anomaly detection is limited without an explicit baseline", True))
        else:
            deviation = current_value - baseline.average
            sigma = baseline.standard_deviation or 0.0
            if sigma > 0 and abs(deviation) > 3 * sigma:
                kind = AnomalyType.TRAFFIC_SPIKE if deviation > 0 else AnomalyType.TRAFFIC_DROP
                anomalies.append(TrafficAnomaly(anomaly_id=f"anomaly:{subject_id}:{metric}:{int(now.timestamp())}", anomaly_type=kind, severity=FindingSeverity.CRITICAL if abs(deviation) > 5 * sigma else FindingSeverity.WARNING, detected_at=now, metric=metric, expected_value=baseline.average, actual_value=current_value, deviation=deviation, possible_causes=["capacity change", "topology or service change", "measurement anomaly"], evidence_ids=baseline.source_evidence_ids, confidence=0.75, incident_creation_recommended=abs(deviation) > 5 * sigma))
        if rate_of_change is not None and abs(rate_of_change) >= 50:
            anomalies.append(TrafficAnomaly(anomaly_id=f"anomaly:{subject_id}:rate:{int(now.timestamp())}", anomaly_type=AnomalyType.TRAFFIC_SPIKE if rate_of_change > 0 else AnomalyType.TRAFFIC_DROP, severity=FindingSeverity.WARNING, detected_at=now, metric=metric, expected_value="stable", actual_value=rate_of_change, deviation=rate_of_change, possible_causes=["sudden traffic change"], confidence=0.5))
        if protocol is not None and expected_protocols and protocol not in expected_protocols:
            anomalies.append(TrafficAnomaly(anomaly_id=f"anomaly:{subject_id}:protocol:{int(now.timestamp())}", anomaly_type=AnomalyType.UNUSUAL_PROTOCOL, severity=FindingSeverity.WARNING, detected_at=now, metric="protocol", expected_value=", ".join(expected_protocols), actual_value=protocol, deviation="unexpected", possible_causes=["new application", "misclassification", "suspicious traffic requires security review"], confidence=0.55))
        self.decisions.append(make_decision("AnomalyDetector", f"anomaly:{subject_id}:{metric}", "baseline_and_signal_checks", "emit anomalies only for explicit deviations or unexpected protocol evidence", ["baseline_and_signal_checks", "infer_anomaly_without_signal"], {"baseline_and_signal_checks": "selected", "infer_anomaly_without_signal": "rejected"}))
        return anomalies
