from domain_packs.pack_activation_guard import PackActivationGuard

def test_activation_guard_blocks_unreviewed_selection():
    result = PackActivationGuard().check({"selected_pack": "banking", "active_packs": ["banking"], "inference_confidence": 1.0, "review_required": True, "review_completed": False})
    assert result["status"] == "blocked"
    assert "required_review_not_completed" in result["reasons"]
