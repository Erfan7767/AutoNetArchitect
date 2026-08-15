"""Central registry and dependency resolver for all configuration templates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import TemplateMetadata, TemplateValidationState, TemplateVariable, TemplateVariableSource


class TemplateRegistry:
    """Index template metadata without assuming universal vendor syntax."""

    def __init__(self, records: Iterable[TemplateMetadata] | None = None) -> None:
        self.records: dict[str, TemplateMetadata] = {record.template_id: record for record in (records or [])}

    @classmethod
    def from_json(cls, path: str | Path) -> "TemplateRegistry":
        """Load the registry JSON and preserve its explicit validation state."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        records = [cls._from_mapping(item) for item in payload.get("templates", [])]
        return cls(records)

    @staticmethod
    def _variable(item: dict[str, object], required: bool) -> TemplateVariable:
        raw_sources = item.get("sources", [])
        sources = tuple(TemplateVariableSource(str(source)) for source in raw_sources) if isinstance(raw_sources, list) else ()
        return TemplateVariable(str(item["name"]), str(item.get("type", item.get("type_name", "string"))), str(item.get("description", "")), required, item.get("default"), sources)

    @classmethod
    def _from_mapping(cls, item: dict[str, object]) -> TemplateMetadata:
        required = tuple(cls._variable(value, True) for value in item.get("required_variables", []) if isinstance(value, dict))
        optional = tuple(cls._variable(value, False) for value in item.get("optional_variables", []) if isinstance(value, dict))
        state = TemplateValidationState(str(item.get("validation_state", TemplateValidationState.BLOCKED.value)))
        return TemplateMetadata(
            template_id=str(item["template_id"]),
            vendor=str(item["vendor"]),
            platform=str(item["platform"]),
            feature_area=str(item["feature_area"]),
            file_path=str(item["file_path"]),
            required_variables=required,
            optional_variables=optional,
            min_platform_version=item.get("min_platform_version"),
            max_platform_version=item.get("max_platform_version"),
            depends_on_templates=tuple(str(value) for value in item.get("depends_on_templates", [])),
            feature_guard_required=str(item.get("feature_guard_required", "")),
            evidence_reference=str(item.get("evidence_reference", "")),
            last_validated_version=str(item.get("last_validated_version", "")),
            validation_state=state,
            description=str(item.get("description", "")),
        )

    def get(self, template_id: str) -> TemplateMetadata | None:
        """Return one template by unique identifier."""
        return self.records.get(template_id)

    def lookup(self, vendor: str, platform: str, feature_area: str) -> list[TemplateMetadata]:
        """Find all templates matching vendor, platform, and feature area."""
        return [record for record in self.records.values() if record.vendor.lower() == vendor.lower() and record.platform.lower() == platform.lower() and record.feature_area.lower() == feature_area.lower()]

    def for_vendor(self, vendor: str) -> list[TemplateMetadata]:
        """List templates belonging to a vendor."""
        return [record for record in self.records.values() if record.vendor.lower() == vendor.lower()]

    def all(self) -> list[TemplateMetadata]:
        """Return all records in deterministic order."""
        return [self.records[key] for key in sorted(self.records)]

    def dependency_order(self, template_ids: Iterable[str]) -> list[TemplateMetadata]:
        """Resolve dependencies using a deterministic topological ordering."""
        requested = set(template_ids)
        unknown = sorted(template_id for template_id in requested if template_id not in self.records)
        if unknown:
            raise KeyError(f"unknown template IDs: {', '.join(unknown)}")
        expanded = set(requested)
        changed = True
        while changed:
            changed = False
            for template_id in list(expanded):
                for dependency in self.records[template_id].depends_on_templates:
                    if dependency not in self.records:
                        raise KeyError(f"template {template_id} depends on unknown template {dependency}")
                    if dependency not in expanded:
                        expanded.add(dependency)
                        changed = True
        ordered: list[str] = []
        temporary: set[str] = set()
        permanent: set[str] = set()

        def visit(template_id: str) -> None:
            if template_id in permanent:
                return
            if template_id in temporary:
                raise ValueError(f"template dependency cycle includes {template_id}")
            temporary.add(template_id)
            for dependency in self.records[template_id].depends_on_templates:
                if dependency in expanded:
                    visit(dependency)
            temporary.remove(template_id)
            permanent.add(template_id)
            ordered.append(template_id)

        for template_id in sorted(expanded):
            visit(template_id)
        return [self.records[template_id] for template_id in ordered]
