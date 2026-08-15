from bootstrap.vendor_workflows.common import BootstrapRequest
from bootstrap.vendor_workflows.fortinet_bootstrap import FortinetBootstrapWorkflow


def test_fortinet_bootstrap_workflow_includes_ha_review():
    artifact = FortinetBootstrapWorkflow().build(BootstrapRequest("fg-1", "fortinet", "fortios", endpoint_reference="human://oob/fg-1", console_available=True))
    assert artifact.vendor == "fortinet"
    assert any(step.step_id == "ha_review" for step in artifact.steps)
    assert artifact.production_deployable is False
