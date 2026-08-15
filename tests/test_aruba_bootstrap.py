from bootstrap.vendor_workflows.aruba_bootstrap import ArubaBootstrapWorkflow
from bootstrap.vendor_workflows.common import BootstrapRequest


def test_aruba_bootstrap_workflow_includes_access_review():
    artifact = ArubaBootstrapWorkflow().build(BootstrapRequest("aruba-1", "aruba", "aoscx", endpoint_reference="human://oob/aruba-1", console_available=True))
    assert artifact.vendor == "aruba"
    assert any(step.step_id == "access_review" for step in artifact.steps)
