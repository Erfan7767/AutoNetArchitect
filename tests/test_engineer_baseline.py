from benchmarking.engineer_baseline import EngineerBaseline, EngineerBaselineRegistry

def test_engineer_baseline_captures_reference_dimensions():
    baseline = EngineerBaseline(baseline_id="b-1", scenario_id="s-1", engineer_reference="human://s-1", design_choices={"topology": "reviewed"}, assumption_quality_score=0.8, unresolved_handling_score=0.9, safety_decision="abstain", config_correctness_score=0.7, evidence_ids=("ev-1",), review_status="validated")
    assert baseline.design_choices and baseline.safety_decision == "abstain" and baseline.config_correctness_score == 0.7

def test_baseline_registry_filters_scenario():
    registry = EngineerBaselineRegistry()
    registry.register(EngineerBaseline(baseline_id="b-2", scenario_id="s-2", engineer_reference="human://s-2"))
    assert registry.for_scenario("s-2")
