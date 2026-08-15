from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_validator import TemplateValidator
from config_generators.models import TemplateValidationState


def test_validator_accepts_syntax_and_marks_unvalidated_templates_preview_only():
    validator = TemplateValidator(TemplateRegistry.from_json(Path("data/template_registry.json")))
    report = validator.validate("cisco_ios_xe.ospf")
    assert report.valid_syntax is True
    assert not report.undeclared_variables
    assert report.status is TemplateValidationState.PREVIEW_ONLY


def test_validator_can_validate_the_complete_registry():
    validator = TemplateValidator(TemplateRegistry.from_json(Path("data/template_registry.json")))
    reports = validator.validate_all()
    assert len(reports) >= 400
    assert all(report.valid_syntax for report in reports)
    assert all(not report.hardcoded_secret_paths for report in reports)
    assert all(not report.hardcoded_ip_literals for report in reports)
