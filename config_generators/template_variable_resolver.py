"""Resolve template variables from governed project sources."""
from __future__ import annotations

from typing import Any

from .models import TemplateMetadata, TemplateVariableSource, VariableResolution
from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderer


class TemplateVariableResolver:
    """Resolve declared variables without inventing values or embedding secrets."""

    SOURCE_ORDER = (
        TemplateVariableSource.DESIGN_ARTIFACT,
        TemplateVariableSource.EQUIPMENT_DATA,
        TemplateVariableSource.HUMAN_SUPPLIED,
        TemplateVariableSource.PROJECT_CONFIGURATION,
        TemplateVariableSource.SECRET_REFERENCE,
    )

    def __init__(self, registry: TemplateRegistry) -> None:
        self.registry = registry

    def resolve(self, template_id: str, sources: dict[str, dict[str, Any]] | None = None, assumptions: dict[str, Any] | None = None) -> VariableResolution:
        """Resolve required and optional variables for a registered template."""
        metadata = self.registry.get(template_id)
        if metadata is None:
            raise KeyError(f"unknown template: {template_id}")
        source_maps = {str(key): dict(value) for key, value in (sources or {}).items() if isinstance(value, dict)}
        assumptions_map = dict(assumptions or {})
        inline_secrets = TemplateRenderer._find_inline_secrets(source_maps)
        if inline_secrets:
            raise ValueError(f"inline secret values are forbidden: {', '.join(inline_secrets)}")
        values: dict[str, Any] = {}
        unresolved: list[str] = []
        defaulted: list[str] = []
        assumed: list[str] = []
        secret_references: list[str] = []
        source_by_variable: dict[str, TemplateVariableSource] = {}
        variables = list(metadata.required_variables) + list(metadata.optional_variables)
        for variable in variables:
            found = False
            for source in self.SOURCE_ORDER:
                source_key = source.value
                source_map = source_maps.get(source_key, {})
                if variable.name in source_map:
                    value = source_map[variable.name]
                    if source is TemplateVariableSource.SECRET_REFERENCE:
                        if not isinstance(value, str) or not value.startswith("secret://"):
                            raise ValueError(f"secret variable {variable.name} must be a secret:// reference")
                        secret_references.append(value)
                    values[variable.name] = value
                    source_by_variable[variable.name] = source
                    found = True
                    break
            if found:
                continue
            if variable.name in assumptions_map:
                values[variable.name] = assumptions_map[variable.name]
                source_by_variable[variable.name] = TemplateVariableSource.ASSUMPTION
                assumed.append(variable.name)
                continue
            if not variable.required and variable.default is not None:
                values[variable.name] = variable.default
                source_by_variable[variable.name] = TemplateVariableSource.DEFAULT
                defaulted.append(variable.name)
                continue
            if variable.required:
                unresolved.append(variable.name)
        return VariableResolution(values, tuple(unresolved), tuple(defaulted), tuple(assumed), tuple(dict.fromkeys(secret_references)), source_by_variable)

    def resolve_from_artifacts(self, template_id: str, design_artifact: dict[str, Any] | None = None, equipment_data: dict[str, Any] | None = None, human_supplied: dict[str, Any] | None = None, project_configuration: dict[str, Any] | None = None, secret_references: dict[str, Any] | None = None, assumptions: dict[str, Any] | None = None) -> VariableResolution:
        """Convenience adapter for the five supported input domains."""
        return self.resolve(template_id, {"design_artifact": design_artifact or {}, "equipment_data": equipment_data or {}, "human_supplied": human_supplied or {}, "project_configuration": project_configuration or {}, "secret_reference": secret_references or {}}, assumptions)
