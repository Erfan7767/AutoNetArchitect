from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_validator import TemplateValidator


def test_paloalto_templates_all_registered_templates_parse():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    validator = TemplateValidator(registry)
    records = [record for record in registry.all() if record.template_id.startswith("paloalto.")]
    assert records
    reports = [validator.validate(record.template_id) for record in records]
    assert all(report.valid_syntax for report in reports)
    assert all(not report.hardcoded_secret_paths for report in reports)
    assert all(not report.hardcoded_ip_literals for report in reports)


def test_paloalto_templates_metadata_has_guard_and_evidence_for_every_template():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    records = [record for record in registry.all() if record.template_id.startswith("paloalto.")]
    assert all(record.feature_guard_required for record in records)
    assert all(record.evidence_reference for record in records)


def test_paloalto_security_policy_contains_required_scoped_lines():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    from config_generators.template_renderer import TemplateRenderer
    output = TemplateRenderer(registry).render("paloalto.security_policy", {"rule_name": "approved-rule", "source_zone": "inside", "destination_zone": "outside", "source_address": "any", "destination_address": "any", "application": "ssl", "service": "service-https", "action": "allow", "log_start": False, "log_end": True, "log_forwarding_profile": "approved-profile"})
    assert 'set rulebase security rules "approved-rule" from inside' in output
    assert "application ssl" in output
    assert "action allow" in output
    assert "log-end true" in output
