from domain_packs.pack_boundary_reporter import PackBoundaryReporter

def test_boundary_report_contains_conflicts_and_review():
    report = PackBoundaryReporter().report({"workflow_id": "w", "selected_pack": "banking", "active_packs": ["banking"], "review_required": True, "review_completed": False}, {"status": "blocked", "production_activation": False, "reasons": ["required_review_not_completed"], "policy": {"conflicts": [], "unknown_packs": []}})
    assert report["activation_status"] == "blocked"
    assert report["review_required"] is True
