from domain_packs.domain_pack_context import DomainPackContext

def test_context_trace_is_serializable():
    trace = DomainPackContext(workflow_id="w1", selected_pack="banking").trace()
    assert trace["workflow_id"] == "w1"
    assert trace["selected_pack"] == "banking"
