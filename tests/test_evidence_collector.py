from troubleshooting.evidence_collector import EvidenceCollector
from troubleshooting.models import AnalysisMode, EvidenceRequest


def test_evidence_collector_supports_offline_and_parsed_modes():
    collector = EvidenceCollector()
    result = collector.collect(AnalysisMode.OFFLINE, design_data={"topology": {"nodes": ["edge-1"]}}, parsed_output=[{"target_device":"edge-1", "output":"up"}])
    assert result.mode == "offline"
    assert len(result.items) == 2
    assert result.items[0].evidence_hash


def test_evidence_collector_live_mode_is_read_only():
    request = EvidenceRequest(evidence_type="interface_state", target_device="edge-1", command_or_query="show interfaces")
    result = EvidenceCollector().collect(AnalysisMode.LIVE_READ_ONLY, [request], live_collector=lambda payload: {"operation":"collect_evidence", "read_only":True, "parsed_data":{"state":"up"}, "confidence":0.8})
    assert result.complete is True
    assert result.items[0].collection_method.value == "live_read_only"


def test_evidence_collector_blocks_missing_live_collector():
    request = EvidenceRequest(evidence_type="interface_state", target_device="edge-1", command_or_query="show interfaces")
    result = EvidenceCollector().collect(AnalysisMode.LIVE_READ_ONLY, [request])
    assert result.complete is False
    assert "interface_state" in result.missing_required
