from config_validators.coverage_tracker import CoverageTracker
from config_validators.syntax_rule_engine import SyntaxRuleEngine


def test_coverage_tracker_reports_uncovered_commands_explicitly():
    results = SyntaxRuleEngine().validate("hostname edge\nvendor-specific-command x\n", "Cisco", "IOS XE")
    report = CoverageTracker().report("Cisco", "IOS XE", results)
    assert report["coverage_percentage"] < 100
    assert "vendor-specific-command x" in report["uncovered_commands"]
    assert "not_covered" in report["coverage_claim"]
