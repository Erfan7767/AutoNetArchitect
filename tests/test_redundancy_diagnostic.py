from troubleshooting.diagnostic_workflows import RedundancyDiagnostic
from troubleshooting.models import EvidenceCollection, EvidenceItem, CollectionMethod, EvidenceSource


def test_redundancy_diagnostic_is_read_only_and_produces_output():
    workflow = RedundancyDiagnostic()
    assert workflow.get_required_commands("cisco", "ios_xe")
    evidence = EvidenceCollection(items=[EvidenceItem(evidence_id="ev-1", source=EvidenceSource.PARSED_OUTPUT, raw_data="state down error deny", parsed_data={"state":"down"}, collection_method=CollectionMethod.PARSED, confidence=0.8)], mode="parsed_output", complete=True)
    output = workflow.execute(evidence, [])
    assert output.workflow_id == workflow.diagnostic_id
    assert output.status == "completed"
    assert output.next_steps
