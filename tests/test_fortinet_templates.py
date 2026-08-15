from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_validator import TemplateValidator


def test_fortinet_templates_all_registered_templates_parse():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    validator = TemplateValidator(registry)
    records = [record for record in registry.all() if record.template_id.startswith("fortinet.")]
    assert records
    reports = [validator.validate(record.template_id) for record in records]
    assert all(report.valid_syntax for report in reports)
    assert all(not report.hardcoded_secret_paths for report in reports)
    assert all(not report.hardcoded_ip_literals for report in reports)


def test_fortinet_templates_metadata_has_guard_and_evidence_for_every_template():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    records = [record for record in registry.all() if record.template_id.startswith("fortinet.")]
    assert all(record.feature_guard_required for record in records)
    assert all(record.evidence_reference for record in records)


def test_fortinet_firewall_policy_contains_required_scoped_lines():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    from config_generators.template_renderer import TemplateRenderer
    output = TemplateRenderer(registry).render("fortinet.firewall_policy", {"policy_id": 10, "policy_name": "approved-policy", "source_zone": "inside", "destination_zone": "outside", "source_address": "all", "destination_address": "all", "service": "HTTPS", "action": "accept", "schedule": "always", "log_traffic": "all"})
    assert "config firewall policy" in output
    assert "edit 10" in output
    assert 'set name "approved-policy"' in output
    assert 'set srcintf "inside"' in output
    assert "next" in output and "end" in output
