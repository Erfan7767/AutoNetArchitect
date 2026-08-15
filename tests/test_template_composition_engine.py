from pathlib import Path

from config_generators.template_composition_engine import TemplateCompositionEngine
from config_generators.template_registry import TemplateRegistry


def test_composition_orders_dependencies_and_deduplicates_output():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    engine = TemplateCompositionEngine(registry)
    result = engine.compose(
        "edge-1",
        "IOS XE",
        ["cisco_ios_xe.device_complete", "cisco_ios_xe.base_system"],
        common_variables={"commands": ["! exact command"]},
        decision_ids=("decision-config",),
    )
    assert result.status == "preview_only"
    assert result.template_ids[0] == "cisco_ios_xe.base_system"
    assert result.rendered_config.count("! exact command") == 1
    assert result.decision_ids == ("decision-config",)


def test_composition_blocks_unavailable_production_validation():
    registry = TemplateRegistry.from_json(Path("data/template_registry.json"))
    engine = TemplateCompositionEngine(registry)
    result = engine.compose("edge-1", "IOS XE", ["cisco_ios_xe.base_system"], common_variables={"commands": ["exact"]}, production=True)
    assert result.status == "blocked_unsupported_templates"
    assert result.rendered_config == ""
    assert result.unsupported_templates == ("cisco_ios_xe.base_system",)
