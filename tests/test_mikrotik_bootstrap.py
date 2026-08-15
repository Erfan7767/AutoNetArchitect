from bootstrap.vendor_workflows.common import BootstrapRequest
from bootstrap.vendor_workflows.mikrotik_bootstrap import MikroTikBootstrapWorkflow


def test_mikrotik_bootstrap_workflow_includes_safe_save_review():
    artifact = MikroTikBootstrapWorkflow().build(BootstrapRequest("mt-1", "mikrotik", "routeros", endpoint_reference="human://oob/mt-1", console_available=True))
    assert artifact.vendor == "mikrotik"
    assert any(step.step_id == "safe_save_review" for step in artifact.steps)
    assert artifact.production_deployable is False
