from bootstrap.vendor_workflows.common import BootstrapRequest
from bootstrap.vendor_workflows.huawei_bootstrap import HuaweiBootstrapWorkflow


def test_huawei_bootstrap_workflow_includes_vrp_review():
    artifact = HuaweiBootstrapWorkflow().build(BootstrapRequest("hw-1", "huawei", "vrp", endpoint_reference="human://oob/hw-1", console_available=True))
    assert artifact.vendor == "huawei"
    assert any(step.step_id == "vrp_review" for step in artifact.steps)
    assert artifact.production_deployable is False
