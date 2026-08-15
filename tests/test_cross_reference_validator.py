from config_validators.cross_reference_validator import CrossReferenceValidator


def test_cross_reference_validator_detects_unresolved_objects():
    text = "interface GigabitEthernet0/0\n ip access-group MISSING in\n service-policy MISSING-POLICY input\n ip vrf forwarding MISSING-VRF\n exit\n"
    diagnostics = CrossReferenceValidator().validate(text, "Cisco", "IOS XE")
    names = {item.referenced_name for item in diagnostics}
    assert "MISSING" in names
    assert "MISSING-POLICY" in names
    assert "MISSING-VRF" in names


def test_cross_reference_validator_accepts_defined_route_map():
    text = "route-map RM permit 10\nrouter ospf 10\n redistribute connected route-map RM\n"
    assert not CrossReferenceValidator().validate(text, "Cisco", "IOS XE")
