from config_validators.deprecated_command_checker import DeprecatedCommandChecker


def test_deprecated_checker_emits_scoped_warning():
    diagnostics = DeprecatedCommandChecker().check("crypto map VPN 10\n", "Cisco", "IOS XE", "17.15")
    assert diagnostics
    assert diagnostics[0].code == "DEPRECATED_COMMAND"
    assert diagnostics[0].metadata["platform_version"] == "17.15"
