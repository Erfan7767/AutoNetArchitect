from config_validators.structural_validator import StructuralValidator


def test_cisco_structure_rejects_orphan_subcommand():
    result = StructuralValidator().validate(" ip address 192.0.2.1 255.255.255.0\n", "Cisco", "IOS XE")
    assert result.valid is False
    assert any(item.code == "ORPHAN_SUBCOMMAND" for item in result.diagnostics)


def test_fortigate_structure_accepts_config_edit_next_end():
    result = StructuralValidator().validate("config system interface\n edit port1\n  set ip 192.0.2.1/30\n next\nend\n", "Fortinet", "FortiOS")
    assert result.valid is True


def test_junos_structure_rejects_unbalanced_brace():
    result = StructuralValidator().validate("set system host-name edge\n{\n", "Juniper", "Junos")
    assert result.valid is False
