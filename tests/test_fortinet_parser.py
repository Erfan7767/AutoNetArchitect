from discovery.parsers.fortinet_parser import FortinetParser


def test_fortinet_parser_extracts_identity():
    parsed = FortinetParser().parse("Version: v7.4.3,build2573\nModel name: FortiGate-100F\nSerial-Number: FGT100F123\nHostname: branch-fw")
    assert parsed.vendor == "fortinet"
    assert parsed.platform == "fortios"
    assert parsed.version == "7.4.3"
    assert parsed.model == "FortiGate-100F"
    assert parsed.serial == "FGT100F123"
    assert parsed.hostname == "branch-fw"
    assert parsed.confidence == "high"
