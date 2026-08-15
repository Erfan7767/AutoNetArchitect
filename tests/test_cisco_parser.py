from discovery.parsers.cisco_parser import CiscoParser


def test_cisco_parser_extracts_identity():
    parsed = CiscoParser().parse("hostname core-1\nCisco IOS XE Software, Version 17.9.4\nModel number : C9300-24T\nProcessor board ID FDO123")
    assert parsed.vendor == "cisco"
    assert parsed.model == "C9300-24T"
    assert parsed.version == "17.9.4"
    assert parsed.serial == "FDO123"
    assert parsed.hostname == "core-1"
    assert parsed.confidence == "high"
