from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_renderer import TemplateRenderError, TemplateRenderer


def build_renderer():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    return TemplateRenderer(registry)


def test_renderer_applies_network_filters_and_records_audit():
    renderer = build_renderer()
    assert renderer._environment().filters["ip_netmask"]("192.0.2.0/24") == "255.255.255.0"
    assert renderer._environment().filters["ip_wildcard"]("192.0.2.0/24") == "0.0.0.255"
    assert renderer._environment().filters["interface_short"]("GigabitEthernet0/0") == "Gi0/0"
    output = renderer.render("cisco_ios_xe.base_system", {"commands": ["! exact command"]}, decision_ids=("decision-1",))
    assert "! exact command" in output
    assert renderer.audit_events[-1].decision_ids == ("decision-1",)


def test_renderer_rejects_inline_secret_and_undefined_variables():
    renderer = build_renderer()
    try:
        renderer.render("cisco_ios_xe.base_system", {"password": "clear-text"})
    except TemplateRenderError:
        pass
    else:
        raise AssertionError("inline secret must be rejected")
    assert renderer._environment().filters["secret_ref"]("secret://device/credential") == "secret://device/credential"
