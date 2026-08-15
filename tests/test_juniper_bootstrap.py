from bootstrap.vendor_workflows.common import BootstrapRequest
from bootstrap.vendor_workflows.juniper_bootstrap import JuniperBootstrapWorkflow


def test_juniper_bootstrap_workflow_includes_commit_review():
    artifact = JuniperBootstrapWorkflow().build(BootstrapRequest("j-1", "juniper", "junos", endpoint_reference="human://oob/j-1", console_available=True))
    assert artifact.vendor == "juniper"
    assert any(step.step_id == "commit_review" for step in artifact.steps)
    assert artifact.remote_destructive_allowed is False
