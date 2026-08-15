"""QoS queue utilization analysis."""
from __future__ import annotations
from typing import Mapping, Sequence
from designers.base_designer import Assumption, DecisionRecord
from ._common import make_assumption, make_decision
from .models import CapacityStatus, QoSQueueFinding

class QoSUtilizationAnalyzer:
    """Compare explicit queue consumption, drops, and allocations."""
    def __init__(self) -> None:
        """Initialize analyzer state."""
        self.decisions: list[DecisionRecord] = []
        self.assumptions: list[Assumption] = []
    def analyze(self, queues: Sequence[Mapping[str, object]], intended_allocations: Mapping[str, float] | None = None) -> list[QoSQueueFinding]:
        """Return queue findings without inferring policy from queue names."""
        intended = dict(intended_allocations or {})
        findings: list[QoSQueueFinding] = []
        for item in queues:
            interface_id = str(item.get("interface_id", ""))
            queue = str(item.get("queue_or_class", ""))
            if not interface_id or not queue:
                self.assumptions.append(make_assumption("qos:queue_identity", "missing", "queue identity is mandatory", True))
                continue
            allocated = float(item["bandwidth_allocated_mbps"]) if item.get("bandwidth_allocated_mbps") is not None else intended.get(queue)
            consumed = float(item["bandwidth_consumed_mbps"]) if item.get("bandwidth_consumed_mbps") is not None else None
            dropped = int(item["packets_dropped"]) if item.get("packets_dropped") is not None else None
            if allocated is None or consumed is None:
                status = CapacityStatus.UNKNOWN
                finding = "allocation or consumption data missing"
            elif dropped and dropped > 0:
                status = CapacityStatus.UPGRADE_REQUIRED
                finding = "queue drops are present"
            elif consumed > allocated:
                status = CapacityStatus.WARNING
                finding = "queue consumption exceeds allocation"
            else:
                status = CapacityStatus.HEALTHY
                finding = "queue consumption is within allocation and no drops were supplied"
            findings.append(QoSQueueFinding(interface_id=interface_id, queue_or_class=queue, queue_depth=float(item["queue_depth"]) if item.get("queue_depth") is not None else None, packets_queued=int(item["packets_queued"]) if item.get("packets_queued") is not None else None, packets_dropped=dropped, bandwidth_consumed_mbps=consumed, bandwidth_allocated_mbps=allocated, status=status, finding=finding, evidence_ids=[str(value) for value in item.get("evidence_ids", [])]))
        self.decisions.append(make_decision("QoSUtilizationAnalyzer", "qos-utilization", "compare_observed_queue_data", "compare explicit observed queues with explicit allocations", ["compare_observed_queue_data", "infer_qos_policy"], {"compare_observed_queue_data": "selected", "infer_qos_policy": "rejected"}))
        return findings
