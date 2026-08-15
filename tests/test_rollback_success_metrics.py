from benchmarking.rollback_success_metrics import RollbackObservation, RollbackSuccessMetrics

def test_rollback_success_metrics_calculates_success_and_scope():
    results = RollbackSuccessMetrics().calculate((RollbackObservation(rollback_id="r-1", required=True, success=True, scope_preserved=True, evidence_ids=("ev-1",)), RollbackObservation(rollback_id="r-2", required=True, success=False, scope_preserved=False, evidence_ids=("ev-2",))))
    values = {item.metric_name: item for item in results}
    assert values["rollback_success_rate"].rate == 0.5 and values["rollback_scope_preservation_rate"].rate == 0.5
