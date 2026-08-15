from traffic_analysis.traffic_scope_boundary import TrafficScopeBoundary

def test_scope_boundary_blocks_dpi_and_allows_capacity():
    boundary = TrafficScopeBoundary()
    assert boundary.check("dpi").status.value == "out_of_scope"
    assert boundary.check("capacity_planning").status.value == "in_scope"

def test_scope_boundary_marks_unknown_preview_only():
    result = TrafficScopeBoundary().check("unknown_subject")
    assert result.preview_only is True
    assert result.status.value == "insufficient_evidence"
