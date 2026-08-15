from benchmarking.reliability_statistics import ReliabilityStatistics

def test_reliability_statistics_returns_bounded_wilson_interval():
    statistic = ReliabilityStatistics().calculate("deployment_success_rate", 8, 10, evidence_ids=("ev-1",))
    assert statistic.rate == 0.8 and 0.0 <= statistic.lower_bound <= statistic.rate <= statistic.upper_bound <= 1.0 and statistic.trials == 10

def test_reliability_statistics_has_no_rate_without_trials():
    assert ReliabilityStatistics().calculate("empty", 0, 0).rate is None
