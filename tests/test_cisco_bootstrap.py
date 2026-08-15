from bootstrap.vendor_workflows.cisco_bootstrap import CiscoBootstrapWorkflow
from bootstrap.vendor_workflows.common import BootstrapRequest


def test_cisco_bootstrap_workflow_builds_family_intents():
    artifact = CiscoBootstrapWorkflow().build(BootstrapRequest("cisco-1", "cisco", "ios_xe", endpoint_reference="human://oob/cisco-1", console_available=True, validated_command_evidence_ids=("cisco-cmd-1",)))
    assert artifact.vendor == "cisco"
    assert any(step.step_id == "capability_review" for step in artifact.steps)
    assert artifact.exact_commands == ()
    assert artifact.production_deployable is False
