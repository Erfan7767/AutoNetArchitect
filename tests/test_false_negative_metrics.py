from benchmarking.false_negative_metrics import AbstentionObservation, FalseNegativeMetrics

def test_false_negative_metrics_calculates_abstention_correctness():
    results = FalseNegativeMetrics().calculate((AbstentionObservation(observation_id="fn-1", system_abstained=True, abstention_was_expected=True, evidence_ids=("ev-1",)), AbstentionObservation(observation_id="fn-2", system_abstained=False, abstention_was_expected=True, unsafe_action_taken=True, evidence_ids=("ev-2",))))
    values = {item.metric_name: item for item in results}
    assert values["abstention_correctness_rate"].rate == 0.5 and values["unsafe_action_miss_rate"].rate == 0.5
