from benchmarking.design_quality_metrics import MetricResult
from benchmarking.scoring_reporter import ScoringReporter

def test_scoring_reporter_allows_only_evidence_bounded_claims():
    report = ScoringReporter().generate(report_id="report-1", corpus_fingerprint="fp-1", run_id="run-1", metrics=(MetricResult(metric_name="design_acceptance_rate", numerator=8, denominator=10, rate=0.8, interpretation="measured", evidence_ids=("ev-1",)), MetricResult(metric_name="empty_metric", numerator=0, denominator=0, interpretation="not measured")))
    claims = {item.metric_name: item for item in report.claims}
    assert claims["design_acceptance_rate"].allowed and not claims["empty_metric"].allowed and "Engineer Review Console" not in ScoringReporter().to_markdown(report)
