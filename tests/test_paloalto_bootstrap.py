from bootstrap.vendor_workflows.common import BootstrapRequest
from bootstrap.vendor_workflows.paloalto_bootstrap import PaloAltoBootstrapWorkflow


def test_paloalto_bootstrap_workflow_includes_policy_review():
    artifact = PaloAltoBootstrapWorkflow().build(BootstrapRequest("pa-1", "paloalto", "panos", endpoint_reference="human://oob/pa-1", console_available=True))
    assert artifact.vendor == "paloalto"
    assert any(step.step_id == "policy_review" for step in artifact.steps)
    assert artifact.remote_destructive_allowed is False
