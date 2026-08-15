from config_validators.completeness_checker import CompletenessChecker


def test_completeness_reports_missing_mandatory_sections():
    diagnostics = CompletenessChecker().check("hostname edge\n", "Cisco", "IOS XE")
    sections = {item.metadata["section_name"] for item in diagnostics}
    assert {"logging", "ntp", "vty", "console", "enable_secret"}.issubset(sections)
