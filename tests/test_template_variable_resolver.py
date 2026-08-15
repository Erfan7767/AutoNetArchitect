from pathlib import Path

from config_generators.template_registry import TemplateRegistry
from config_generators.template_variable_resolver import TemplateVariableResolver


def test_resolver_tracks_sources_and_unresolved_variables():
    resolver = TemplateVariableResolver(TemplateRegistry.from_json(Path("data/template_registry.json")))
    result = resolver.resolve_from_artifacts(
        "cisco_ios_xe.ospf",
        design_artifact={"ospf_process_id": 10, "router_id": "192.0.2.1"},
        secret_references={"secret_references": "secret://device/credential"},
        assumptions={"reference_bandwidth": 100000},
    )
    assert result.unresolved == ()
    assert result.values["ospf_process_id"] == 10
    assert "reference_bandwidth" in result.assumed
    assert result.secret_references == ("secret://device/credential",)


def test_resolver_reports_missing_required_variable():
    resolver = TemplateVariableResolver(TemplateRegistry.from_json(Path("data/template_registry.json")))
    result = resolver.resolve("cisco_ios_xe.ospf", {"design_artifact": {"ospf_process_id": 10}})
    assert "router_id" in result.unresolved
