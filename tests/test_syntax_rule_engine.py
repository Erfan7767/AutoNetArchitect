from config_validators.syntax_rule_engine import SyntaxRuleEngine
from config_validators.models import CoverageStatus


def test_syntax_engine_validates_known_commands_and_marks_unknown_scope():
    engine = SyntaxRuleEngine()
    known = engine.validate_line("hostname edge-1", 1, "Cisco", "IOS XE")
    unknown = engine.validate_line("vendor-specific-command x", 2, "Cisco", "IOS XE")
    assert known.valid is True
    assert unknown.valid is True
    assert unknown.coverage_status is CoverageStatus.NOT_COVERED
    assert unknown.diagnostics[0].code == "SYNTAX_NOT_COVERED"


def test_syntax_engine_rejects_explicit_invalid_command():
    result = SyntaxRuleEngine().validate_line("THIS-IS-NOT-VALID", 1, "Cisco", "IOS XE")
    assert result.valid is False
    assert result.diagnostics[0].code == "UNKNOWN_COMMAND"
