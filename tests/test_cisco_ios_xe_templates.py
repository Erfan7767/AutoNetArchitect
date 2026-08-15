from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_validator import TemplateValidator


def test_cisco_ios_xe_templates_all_registered_templates_parse():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    validator = TemplateValidator(registry)
    records = [record for record in registry.all() if record.template_id.startswith("cisco_ios_xe.")]
    assert records
    reports = [validator.validate(record.template_id) for record in records]
    assert all(report.valid_syntax for report in reports)
    assert all(not report.hardcoded_secret_paths for report in reports)
    assert all(not report.hardcoded_ip_literals for report in reports)


def test_cisco_ios_xe_templates_metadata_has_guard_and_evidence_for_every_template():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    records = [record for record in registry.all() if record.template_id.startswith("cisco_ios_xe.")]
    assert all(record.feature_guard_required for record in records)
    assert all(record.evidence_reference for record in records)


def test_cisco_ios_xe_ospf_contains_required_guarded_commands():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    from config_generators.template_renderer import TemplateRenderer
    output = TemplateRenderer(registry).render("cisco_ios_xe.ospf", {"ospf_process_id": 10, "router_id": "192.0.2.1", "reference_bandwidth": 100000, "passive_interface_default": True, "no_passive_interfaces": ["Gi0/0"], "networks": [{"prefix": "192.0.2.0", "wildcard": "0.0.0.255", "area": 0}], "decision_ids": ["decision-ospf"]})
    assert "router ospf 10" in output
    assert "router-id 192.0.2.1" in output
    assert "passive-interface default" in output
    assert "no passive-interface Gi0/0" in output
