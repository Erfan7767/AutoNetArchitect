from troubleshooting.packet_path_analyzer import PacketPathAnalyzer


def test_packet_path_analyzer_detects_acl_drop_point():
    result = PacketPathAnalyzer().analyze("10.0.0.1", "10.0.1.1", "tcp", 443, design_data={"path_hops":[{"device_id":"fw-1", "decision":"drop", "acl_action":"deny"}]})
    assert result.drop_point is not None
    assert result.filtered_by == ["fw-1"]
    assert result.confidence > 0.0


def test_packet_path_analyzer_marks_missing_hops_as_assumption():
    result = PacketPathAnalyzer().analyze("10.0.0.1", "10.0.1.1", "icmp")
    assert result.hops == []
    assert result.assumptions
