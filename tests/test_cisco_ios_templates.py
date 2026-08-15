from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_validator import TemplateValidator


def test_cisco_ios_templates_all_registered_templates_parse():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    validator = TemplateValidator(registry)
    records = [record for record in registry.all() if record.template_id.startswith("cisco_ios.")]
    assert records
    reports = [validator.validate(record.template_id) for record in records]
    assert all(report.valid_syntax for report in reports)
    assert all(not report.hardcoded_secret_paths for report in reports)
    assert all(not report.hardcoded_ip_literals for report in reports)


def test_cisco_ios_templates_metadata_has_guard_and_evidence_for_every_template():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    records = [record for record in registry.all() if record.template_id.startswith("cisco_ios.")]
    assert all(record.feature_guard_required for record in records)
    assert all(record.evidence_reference for record in records)
