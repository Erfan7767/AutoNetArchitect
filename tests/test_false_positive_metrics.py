from benchmarking.false_positive_metrics import FalsePositiveMetrics, FalsePositiveObservation

def test_false_positive_metrics_calculates_unsafe_and_unsupported_rates():
    results = FalsePositiveMetrics().calculate((FalsePositiveObservation(observation_id="fp-1", recommendation_made=True, recommendation_was_unsafe=True, unsupported_claim_made=True, reference_expected_safe=True, evidence_ids=("ev-1",)), FalsePositiveObservation(observation_id="fp-2", recommendation_made=True, recommendation_was_unsafe=False, unsupported_claim_made=False, reference_expected_safe=True, evidence_ids=("ev-2",))))
    values = {item.metric_name: item for item in results}
    assert values["unsafe_recommendation_rate"].rate == 0.5 and values["unsupported_claim_rate"].rate == 0.5
