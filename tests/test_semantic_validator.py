from config_validators.semantic_validator import SemanticValidator


def test_semantic_validator_detects_invalid_network_values():
    text = "interface GigabitEthernet0/0\n ip address 999.999.999.999 255.0.255.0\n exit\nvlan 5000\nrouter bgp 0\nspanning-tree vlan 10 priority 123\n"
    diagnostics = SemanticValidator().validate(text, "Cisco", "IOS XE")
    codes = {item.code for item in diagnostics}
    assert {"INVALID_INTERFACE_IP", "INVALID_NETMASK", "INVALID_VLAN", "INVALID_ASN", "INVALID_STP_PRIORITY"}.issubset(codes)
