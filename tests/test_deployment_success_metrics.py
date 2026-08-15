from benchmarking.deployment_success_metrics import DeploymentObservation, DeploymentSuccessMetrics

def test_deployment_success_metrics_calculates_success_and_unsafe_rate():
    results = DeploymentSuccessMetrics().calculate((DeploymentObservation(deployment_id="d-1", success=True, evidence_ids=("ev-1",)), DeploymentObservation(deployment_id="d-2", success=False, unsafe_recommendation=True, evidence_ids=("ev-2",))))
    values = {item.metric_name: item for item in results}
    assert values["deployment_success_rate"].rate == 0.5 and values["unsafe_recommendation_rate"].rate == 0.5
