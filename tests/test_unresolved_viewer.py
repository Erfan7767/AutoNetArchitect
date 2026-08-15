from review_console.unresolved_viewer import UnresolvedCategory, UnresolvedViewer

def test_unresolved_viewer_categorizes_all_required_inputs():
    rows = UnresolvedViewer().build(human_mandatory=({"key": "isp_handoff", "description": "ISP handoff missing"},), assumptions=({"key": "mount_height", "description": "unknown"},), insufficient_evidence=({"item_id": "e-1", "description": "RF survey absent"},), scope_issues=({"item_id": "s-1", "description": "unsupported protocol"},))
    assert {row.category for row in rows} == {UnresolvedCategory.HUMAN_SUPPLIED_MANDATORY, UnresolvedCategory.ASSUMPTION, UnresolvedCategory.INSUFFICIENT_EVIDENCE, UnresolvedCategory.SCOPE_BOUNDARY}
