from discovery.parsers.juniper_parser import JuniperParser


def test_juniper_parser_extracts_identity():
    parsed = JuniperParser().parse("Model: EX4300\nJunos: 21.4R3\nChassis serial number: JN123456\nset system host-name distribution-1")
    assert parsed.vendor == "juniper"
    assert parsed.platform == "junos"
    assert parsed.version == "21.4R3"
    assert parsed.model == "EX4300"
    assert parsed.serial == "JN123456"
    assert parsed.hostname == "distribution-1"
    assert parsed.confidence == "high"
