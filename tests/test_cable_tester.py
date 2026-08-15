from verification.cable_tester import CableTester


def test_cable_tester_evaluates_explicit_results_only():
    tester = CableTester()
    assert tester.evaluate(None).proof_status == "not_verifiable_with_current_inputs"
    report = tester.evaluate({"cable-1": {"status": "passed", "remote_port": "sw-2:Gi1/0/1", "evidence_ids": ["cable-e1"]}})
    assert report.proof_status == "verified"
    assert report.production_suitable is True
    failed = tester.evaluate({"cable-2": {"status": "failed"}})
    assert failed.proof_status == "failed"
    assert failed.production_suitable is False
