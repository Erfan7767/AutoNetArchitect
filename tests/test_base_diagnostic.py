from troubleshooting.diagnostic_workflows.base_diagnostic import BaseDiagnostic
from troubleshooting.models import EvidenceCollection


class ExampleDiagnostic(BaseDiagnostic):
    """Small read-only workflow used to test base contracts."""

    diagnostic_id = "example"
    symptom_class = "example"

    def execute(self, evidence, hypotheses=()):
        """Use the common output builder."""
        return self._build_output(evidence, hypotheses, ["example finding"])


def test_base_diagnostic_requires_read_only_workflow_implementation():
    workflow = ExampleDiagnostic()
    output = workflow.execute(EvidenceCollection(mode="offline", complete=False))
    assert output.workflow_id == "example"
    assert output.status == "partially_completed"
    assert output.next_steps[0].blocked is True


def test_base_diagnostic_returns_only_read_only_command_catalogue():
    workflow = ExampleDiagnostic()
    assert all(command for command in workflow.get_required_commands("cisco", "ios_xe"))
