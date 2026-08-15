from discovery.parsers.mikrotik_parser import MikroTikParser


def test_mikrotik_parser_extracts_identity():
    parsed = MikroTikParser().parse("version: 7.14\nboard-name: CRS326-24G-2S+\nserial-number: ABC123\nname: lab-switch")
    assert parsed.vendor == "mikrotik"
    assert parsed.platform == "routeros"
    assert parsed.version == "7.14"
    assert parsed.model == "CRS326-24G-2S+"
    assert parsed.serial == "ABC123"
    assert parsed.hostname == "lab-switch"
    assert parsed.confidence == "high"
