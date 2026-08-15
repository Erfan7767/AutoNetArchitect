from discovery.parsers.paloalto_parser import PaloAltoParser


def test_paloalto_parser_extracts_identity():
    parsed = PaloAltoParser().parse("sw-version: 11.1.0\nmodel: PA-3220\nserial: 0123456789\nhostname: edge-fw")
    assert parsed.vendor == "paloalto"
    assert parsed.platform == "panos"
    assert parsed.version == "11.1.0"
    assert parsed.model == "PA-3220"
    assert parsed.serial == "0123456789"
    assert parsed.hostname == "edge-fw"
    assert parsed.confidence == "high"
