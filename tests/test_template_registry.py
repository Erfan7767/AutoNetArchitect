from pathlib import Path

from config_generators.template_registry import TemplateRegistry


def test_registry_loads_complete_template_set_and_resolves_dependencies():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    assert len(registry.all()) >= 400
    assert registry.get("cisco_ios_xe.ospf") is not None
    assert registry.lookup("Cisco", "IOS XE", "routing.ospf")
    ordered = registry.dependency_order(["cisco_ios_xe.device_complete"])
    identifiers = [record.template_id for record in ordered]
    assert identifiers.index("cisco_ios_xe.base_system") < identifiers.index("cisco_ios_xe.device_complete")


def test_registry_rejects_unknown_template_dependency_request():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    try:
        registry.dependency_order(["unknown.template"])
    except KeyError:
        return
    raise AssertionError("unknown template should be rejected")
