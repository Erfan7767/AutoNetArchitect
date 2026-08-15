from discovery.parsers.aruba_parser import ArubaParser


def test_aruba_parser_extracts_identity():
    parsed = ArubaParser().parse("ArubaOS-CX 10.10.1\nProduct Name : JL658A\nSerial Number : CN123456\nHostname : access-1")
    assert parsed.vendor == "aruba"
    assert parsed.platform == "aoscx"
    assert parsed.version == "10.10.1"
    assert parsed.model == "JL658A"
    assert parsed.serial == "CN123456"
    assert parsed.hostname == "access-1"
    assert parsed.confidence == "high"
