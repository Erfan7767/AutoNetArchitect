from verification.connectivity_tester import ConnectivityTester


def test_connectivity_tester_evaluates_paths_without_active_probes():
    tester = ConnectivityTester()
    assert tester.verify({"path-1": {"max_latency_ms": 20}}, None).proof_status == "not_verifiable_with_current_inputs"
    report = tester.verify({"path-1": {"max_latency_ms": 20, "max_packet_loss_pct": 1}}, {"path-1": {"status": "reachable", "latency_ms": 5, "packet_loss_pct": 0, "evidence_ids": ["path-e1"]}})
    assert report.proof_status == "verified"
    exceeded = tester.verify({"path-1": {"max_latency_ms": 20}}, {"path-1": {"status": "reachable", "latency_ms": 40}})
    assert exceeded.proof_status == "failed"
