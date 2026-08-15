from troubleshooting.correlation_engine import CorrelationEngine


def test_correlation_engine_links_same_device_and_time():
    report = CorrelationEngine().correlate([{"evidence_id":"e1", "device_id":"r1", "timestamp":"2026-01-01T00:00:00+00:00"}, {"evidence_id":"e2", "device_id":"r1", "timestamp":"2026-01-01T00:01:00+00:00"}])
    assert report.links
    assert all(link.causal_claim is False for link in report.links)


def test_correlation_engine_has_no_causal_claim_without_records():
    report = CorrelationEngine().correlate([])
    assert report.links == []
    assert report.confidence == 0.0
