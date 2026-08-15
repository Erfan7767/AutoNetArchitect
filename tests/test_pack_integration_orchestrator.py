from domain_packs.pack_integration_orchestrator import PackIntegrationOrchestrator

def test_orchestrator_links_paths_and_blocks_pending_review():
    result = PackIntegrationOrchestrator().integrate({"workflow_id": "w1", "sector": "banking", "review_completed": False})
    assert result["selection"]["selected_pack"] == "banking"
    assert result["activation"]["status"] == "blocked"
    assert result["paths"]["deployment"] == "activation_guard_required"
