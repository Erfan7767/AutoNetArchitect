from discovery.parsers.huawei_parser import HuaweiParser


def test_huawei_parser_extracts_identity():
    parsed = HuaweiParser().parse("<core-1>\nVRP (R) software, Version 8.180\nMODEL : S5735\nESN: 2102350ABC\nsysname core-1")
    assert parsed.vendor == "huawei"
    assert parsed.platform == "vrp"
    assert parsed.version == "8.180"
    assert parsed.model == "S5735"
    assert parsed.serial == "2102350ABC"
    assert parsed.hostname == "core-1"
    assert parsed.confidence == "high"
