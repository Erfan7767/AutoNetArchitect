from datetime import datetime, timezone, timedelta
from traffic_analysis.traffic_collector import CollectionRequest, TrafficCollector
from traffic_analysis.models import TrafficSample

def test_traffic_collector_accepts_read_only_snmp_samples():
    sample = TrafficSample(timestamp=datetime.now(timezone.utc), interface_id="r1:Gi1", in_octets=100, out_octets=200, evidence_id="ev-1")
    result = TrafficCollector().collect_snmp(CollectionRequest(target_ids=["r1"], method="snmp_counters"), [sample])
    assert result.evidence_ids == ["ev-1"]

def test_traffic_collector_rejects_non_read_only():
    try:
        TrafficCollector().collect_snmp(CollectionRequest(target_ids=["r1"], method="snmp_counters", read_only=False), [])
    except ValueError as error:
        assert "read_only" in str(error)
    else:
        raise AssertionError("non-read-only traffic collection must be rejected")

def test_counter_rate_uses_delta():
    previous = TrafficSample(timestamp=datetime.now(timezone.utc), interface_id="i", in_octets=0, out_octets=0, evidence_id="e1")
    current = previous.model_copy(update={"in_octets":1000, "out_octets":2000, "evidence_id":"e2"})
    rates = TrafficCollector.counter_rate(previous, current, timedelta(seconds=10))
    assert rates["in_bps"] == 800.0
