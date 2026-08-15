from benchmarking.design_quality_metrics import DesignQualityMetrics, DesignQualityObservation

def test_design_quality_metrics_calculates_acceptance_and_assumption_metrics():
    results = DesignQualityMetrics().calculate((DesignQualityObservation(scenario_id="s-1", design_accepted=True, design_choice_match=True, assumption_quality_score=0.8, unresolved_handling_correct=True, config_correctness_score=0.9, evidence_ids=("ev-1",)), DesignQualityObservation(scenario_id="s-2", design_accepted=False, design_choice_match=False, assumption_quality_score=0.4, unresolved_handling_correct=False, evidence_ids=("ev-2",))))
    values = {item.metric_name: item for item in results}
    assert values["design_acceptance_rate"].rate == 0.5 and abs(values["assumption_quality_mean"].mean - 0.6) < 1e-9 and abs(values["config_correctness_mean"].mean - 0.9) < 1e-9
