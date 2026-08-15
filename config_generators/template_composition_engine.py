"""Compose registered template fragments into a device configuration."""
from __future__ import annotations

from typing import Any, Iterable

from .models import CompositionResult
from .template_registry import TemplateRegistry
from .template_renderer import TemplateRenderError, TemplateRenderer


class TemplateCompositionEngine:
    """Build a traceable configuration from ordered, registered template fragments."""

    DEFAULT_ORDER = (
        "base_system", "hostname_domain", "aaa", "local_users", "logging", "ntp", "snmp",
        "interface", "vlan", "stp", "routing", "ospf", "eigrp", "isis", "bgp", "static_routes",
        "route_map", "prefix_list", "acl", "nat", "hsrp", "vrrp", "glbp", "dhcp", "qos", "dot1x",
        "radius", "tacacs", "vpn", "crypto", "hardening", "banner", "device_complete",
    )

    def __init__(self, registry: TemplateRegistry, renderer: TemplateRenderer | None = None) -> None:
        self.registry = registry
        self.renderer = renderer or TemplateRenderer(registry)

    def _ordered_ids(self, template_ids: Iterable[str]) -> list[str]:
        requested = list(dict.fromkeys(template_ids))
        records = self.registry.dependency_order(requested)
        rank = {token: index for index, token in enumerate(self.DEFAULT_ORDER)}
        return [record.template_id for record in sorted(records, key=lambda record: (rank.get(record.template_id.rsplit('.', 1)[-1], 1000), record.template_id))]

    @staticmethod
    def _dedupe_lines(text: str) -> str:
        seen: set[str] = set()
        output: list[str] = []
        for line in text.splitlines():
            key = line.rstrip()
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            output.append(line.rstrip())
        return "\n".join(output).strip() + ("\n" if output else "")

    def compose(self, device_id: str, platform: str, template_ids: Iterable[str], variables_by_template: dict[str, dict[str, Any]] | None = None, common_variables: dict[str, Any] | None = None, decision_ids: tuple[str, ...] = (), production: bool = False) -> CompositionResult:
        """Compose templates while exposing blocked fragments instead of hiding them."""
        ordered_ids = self._ordered_ids(template_ids)
        variables_map = variables_by_template or {}
        common = dict(common_variables or {})
        rendered_parts: list[str] = []
        unsupported: list[str] = []
        evidence: list[str] = []
        events_before = len(self.renderer.audit_events)
        for template_id in ordered_ids:
            metadata = self.registry.get(template_id)
            if metadata is None:
                unsupported.append(template_id)
                continue
            variables = dict(common)
            variables.update(variables_map.get(template_id, {}))
            try:
                rendered_parts.append(self.renderer.render(template_id, variables, decision_ids, production))
                evidence.append(metadata.evidence_reference)
            except TemplateRenderError:
                unsupported.append(template_id)
        rendered = self._dedupe_lines("\n".join(part for part in rendered_parts if part.strip()))
        new_events = tuple(self.renderer.audit_events[events_before:])
        if unsupported:
            status = "blocked_unsupported_templates" if production else "preview_with_unsupported_templates"
            rendered = ""
        elif not ordered_ids:
            status = "empty_composition"
        elif any(self.registry.get(template_id) and self.registry.get(template_id).validation_state.value != "verified" for template_id in ordered_ids):
            status = "preview_only"
        else:
            status = "composed"
        return CompositionResult(device_id, platform, status, rendered, tuple(ordered_ids), decision_ids, tuple(dict.fromkeys(evidence)), tuple(unsupported), new_events)
